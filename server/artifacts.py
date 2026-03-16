"""Utilities for temporary extraction artifacts and downloadable packages."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from models.normalized import FullPageNormalizedOutput, NormalizedOutput
from models.requests import ExtractionRequest

PACKAGE_PROMPT_PREAMBLE = """Before building, inspect the files in this package as context.
1. Read README.md and manifest.json first.
2. Use normalized.json as the structured source of truth.
3. Inspect the primary screenshot, the sections/ folder, and the assets/, rich_media/, animations/, and animations/scroll_probe/ folders.
4. If package files and the prompt disagree, prioritize manifest.json, normalized.json, and the primary screenshot."""


@dataclass(slots=True)
class PackagedArtifacts:
    """Paths and serialized payloads for one packaged extraction."""

    workspace_dir: Path
    package_path: Path
    package_filename: str
    prompt_text: str
    normalized_payload: dict[str, Any]
    manifest_payload: dict[str, Any]


def artifact_root() -> Path:
    """Return the temp root used for extraction workspaces."""
    root = Path(tempfile.gettempdir()) / "component-extractor"
    root.mkdir(parents=True, exist_ok=True)
    return root


def reset_artifact_root() -> None:
    """Delete stale task artifacts from previous app runs."""
    root = artifact_root()
    for child in root.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def create_task_workspace(task_id: str) -> Path:
    """Create a clean temporary workspace for a task."""
    workspace_dir = artifact_root() / task_id
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir, ignore_errors=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    return workspace_dir


def cleanup_task_workspace(workspace_dir: Path | str | None) -> None:
    """Remove the temporary workspace for a task."""
    if not workspace_dir:
        return

    shutil.rmtree(Path(workspace_dir), ignore_errors=True)


def build_task_artifact_url(
    task_id: str,
    workspace_dir: Path | str | None,
    artifact_path: str | Path | None,
) -> str | None:
    """Convert an absolute artifact path into a task-scoped preview URL."""
    relative_path = relative_artifact_path(workspace_dir, artifact_path)
    if not relative_path:
        return None
    return f"/api/extract/{task_id}/artifacts/{relative_path}"


def relative_artifact_path(
    workspace_dir: Path | str | None,
    artifact_path: str | Path | None,
) -> str | None:
    """Convert an artifact path to a workspace-relative path when possible."""
    if not workspace_dir or not artifact_path:
        return None

    try:
        base_dir = Path(workspace_dir).resolve()
        candidate = Path(artifact_path)
        if not candidate.is_absolute():
            return candidate.as_posix()
        return candidate.resolve().relative_to(base_dir).as_posix()
    except Exception:
        return None


def package_extraction_result(
    task_id: str,
    request: ExtractionRequest,
    workspace_dir: Path,
    normalized: NormalizedOutput | FullPageNormalizedOutput,
    synthesis_prompt: str,
) -> PackagedArtifacts:
    """Write package support files and archive the workspace into a ZIP."""
    normalized_payload = build_packaged_normalized_payload(normalized, workspace_dir)
    prompt_text = build_package_prompt_text(synthesis_prompt)
    readme_text = build_package_readme(request.mode)

    _write_text(workspace_dir / "prompt.txt", prompt_text)
    _write_text(workspace_dir / "README.md", readme_text)
    _write_json(workspace_dir / "normalized.json", normalized_payload)

    manifest_payload = build_package_manifest(
        task_id=task_id,
        request=request,
        normalized_payload=normalized_payload,
        workspace_dir=workspace_dir,
    )
    _write_json(workspace_dir / "manifest.json", manifest_payload)

    package_filename = f"component-extractor-{task_id}.zip"
    package_path = workspace_dir / package_filename
    _create_archive(workspace_dir, package_path)

    return PackagedArtifacts(
        workspace_dir=workspace_dir,
        package_path=package_path,
        package_filename=package_filename,
        prompt_text=prompt_text,
        normalized_payload=normalized_payload,
        manifest_payload=manifest_payload,
    )


def build_packaged_normalized_payload(
    normalized: NormalizedOutput | FullPageNormalizedOutput,
    workspace_dir: Path,
) -> dict[str, Any]:
    """Serialize normalized data using package-relative file paths."""
    payload = normalized.model_dump(mode="json")

    if payload.get("mode") == "component":
        payload["target"]["screenshot_path"] = relative_artifact_path(
            workspace_dir,
            payload["target"].get("screenshot_path"),
        )
    else:
        payload["page_capture"]["screenshot_path"] = relative_artifact_path(
            workspace_dir,
            payload["page_capture"].get("screenshot_path"),
        )

    for asset in payload.get("assets", []):
        asset["local_path"] = relative_artifact_path(
            workspace_dir,
            asset.get("local_path"),
        )

    recording = payload.get("animations", {}).get("recording")
    if recording:
        recording["video_path"] = relative_artifact_path(
            workspace_dir,
            recording.get("video_path"),
        )
        recording["frames_dir"] = relative_artifact_path(
            workspace_dir,
            recording.get("frames_dir"),
        )

    scroll_probe = payload.get("animations", {}).get("scroll_probe")
    if scroll_probe:
        scroll_probe["video_path"] = relative_artifact_path(
            workspace_dir,
            scroll_probe.get("video_path"),
        )
        scroll_probe["frames_dir"] = relative_artifact_path(
            workspace_dir,
            scroll_probe.get("frames_dir"),
        )

    for media in payload.get("rich_media", []):
        media["snapshot_path"] = relative_artifact_path(
            workspace_dir,
            media.get("snapshot_path"),
        )

    for section in payload.get("page_capture", {}).get("sections", []):
        section["screenshot_path"] = relative_artifact_path(
            workspace_dir,
            section.get("screenshot_path"),
        )
        section_probe = (section.get("animations") or {}).get("scroll_probe")
        if section_probe:
            section_probe["video_path"] = relative_artifact_path(
                workspace_dir,
                section_probe.get("video_path"),
            )
            section_probe["frames_dir"] = relative_artifact_path(
                workspace_dir,
                section_probe.get("frames_dir"),
            )
        for media in section.get("rich_media", []):
            media["snapshot_path"] = relative_artifact_path(
                workspace_dir,
                media.get("snapshot_path"),
            )

    return payload


def build_package_prompt_text(synthesis_prompt: str) -> str:
    """Prepend package-usage instructions to the AI-generated prompt."""
    cleaned_prompt = synthesis_prompt.strip()
    if not cleaned_prompt:
        return PACKAGE_PROMPT_PREAMBLE
    return f"{PACKAGE_PROMPT_PREAMBLE}\n\n{cleaned_prompt}"


def build_package_readme(mode: str) -> str:
    """Generate a short human-readable guide for the package."""
    scope_label = "component" if mode == "component" else "landing page"
    return (
        "# Component Extractor Package\n\n"
        f"This package contains the collected context for one {scope_label} extraction.\n\n"
        "Recommended order of use:\n"
        "1. Open `manifest.json` for the inventory and summary.\n"
        "2. Read `normalized.json` for structured data.\n"
        "3. Inspect the primary screenshot, the `sections/` folder, and the `assets/`, `rich_media/`, `animations/`, and `animations/scroll_probe/` folders.\n"
        "4. Paste `prompt.txt` into your coding AI as the starting instruction.\n\n"
        "If the files disagree, prioritize `manifest.json`, `normalized.json`, and the primary screenshot.\n"
    )


def _build_section_manifest_entry(section: dict[str, Any]) -> dict[str, Any]:
    """Build the manifest entry for one section-scoped capture."""
    animations = section.get("animations") or {}
    scroll_probe = animations.get("scroll_probe", {})
    return {
        "section_id": section.get("section_id"),
        "name": section.get("name"),
        "selector": section.get("selector"),
        "screenshot_path": section.get("screenshot_path"),
        "scroll_effects": animations.get("scroll_effects", []),
        "scroll_probe": {
            "triggered": scroll_probe.get("triggered", False),
            "video_path": scroll_probe.get("video_path"),
            "frames_dir": scroll_probe.get("frames_dir"),
            "observations": scroll_probe.get("observations", []),
        },
        "rich_media": [
            {
                "type": media.get("type"),
                "selector": media.get("selector"),
                "snapshot_path": media.get("snapshot_path"),
            }
            for media in section.get("rich_media", [])
        ],
        "collection_limitations": section.get("collection_limitations", []),
    }


def build_package_manifest(
    task_id: str,
    request: ExtractionRequest,
    normalized_payload: dict[str, Any],
    workspace_dir: Path,
) -> dict[str, Any]:
    """Build the manifest.json payload for the downloadable package."""
    scroll_probe = normalized_payload.get("animations", {}).get("scroll_probe") or {}
    sections = normalized_payload.get("page_capture", {}).get("sections", [])
    screenshot_path = (
        normalized_payload.get("target", {}).get("screenshot_path")
        if normalized_payload.get("mode") == "component"
        else normalized_payload.get("page_capture", {}).get("screenshot_path")
    )
    files = sorted(_list_workspace_files(workspace_dir) + ["manifest.json"])
    files = list(dict.fromkeys(files))

    return {
        "task_id": task_id,
        "mode": normalized_payload.get("mode"),
        "source_url": request.url,
        "strategy": request.strategy,
        "query": request.query,
        "created_at": datetime.now(UTC).isoformat(),
        "entrypoints": {
            "prompt": "prompt.txt",
            "readme": "README.md",
            "manifest": "manifest.json",
            "normalized": "normalized.json",
            "primary_screenshot": screenshot_path,
        },
        "summary": {
            "asset_count": len(normalized_payload.get("assets", [])),
            "rich_media_count": len(normalized_payload.get("rich_media", [])),
            "library_count": len(normalized_payload.get("external_libraries", [])),
            "scroll_probe_triggered": scroll_probe.get("triggered", False),
            "section_count": len(sections),
            "animated_section_count": sum(
                1
                for section in sections
                if (section.get("animations") or {}).get("scroll_effects")
                or ((section.get("animations") or {})
                .get("scroll_probe", {})
                .get("triggered", False))
                or section.get("rich_media")
            ),
        },
        "collection_limitations": normalized_payload.get("collection_limitations", []),
        "assets": [
            {
                "type": asset.get("type"),
                "original_url": asset.get("original_url"),
                "path": asset.get("local_path"),
            }
            for asset in normalized_payload.get("assets", [])
        ],
        "rich_media": [
            {
                "type": media.get("type"),
                "selector": media.get("selector"),
                "snapshot_path": media.get("snapshot_path"),
            }
            for media in normalized_payload.get("rich_media", [])
        ],
        "scroll_probe": {
            "video_path": scroll_probe.get("video_path"),
            "frames_dir": scroll_probe.get("frames_dir"),
            "step_count": scroll_probe.get("step_count"),
            "observations": scroll_probe.get("observations", []),
        },
        "sections": [_build_section_manifest_entry(section) for section in sections],
        "files": files,
    }


def _create_archive(workspace_dir: Path, package_path: Path) -> None:
    """Archive the entire workspace into a ZIP file."""
    with zipfile.ZipFile(
        package_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in workspace_dir.rglob("*"):
            if not path.is_file() or path == package_path:
                continue
            archive.write(path, path.relative_to(workspace_dir))


def _list_workspace_files(workspace_dir: Path) -> list[str]:
    """Return all current workspace files relative to the workspace root."""
    files: list[str] = []
    for path in workspace_dir.rglob("*"):
        if path.is_file() and path.name != "manifest.json":
            files.append(path.relative_to(workspace_dir).as_posix())
    return files


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON file with UTF-8 encoding."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    """Write a plain text file with UTF-8 encoding."""
    path.write_text(content.strip() + "\n", encoding="utf-8")
