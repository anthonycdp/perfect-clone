"""Extraction runner for async pipeline execution."""

import os
from pathlib import Path

from models.errors import ExtractionError
from server.artifacts import (
    build_task_artifact_url,
    create_task_workspace,
    package_extraction_result,
)
from server.task import ExtractionTask


async def run_extraction(task: ExtractionTask):
    """Execute the extraction pipeline for a task."""
    task.workspace_dir = create_task_workspace(task.id)

    try:
        from orchestrator import ExtractionOrchestrator

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await task.emit_progress(
                0,
                "error",
                "OPENAI_API_KEY not configured",
                done=True,
            )
            return

        def progress_callback(step: int, step_name: str, message: str):
            import asyncio

            asyncio.create_task(task.emit_progress(step, step_name, message))

        orchestrator = ExtractionOrchestrator(
            api_key=api_key,
            output_dir=str(task.workspace_dir),
        )
        synthesis = await orchestrator.extract(
            url=task.request.url,
            extraction_mode=task.request.mode,
            strategy=task.request.strategy,
            query=task.request.query,
            progress_callback=progress_callback,
            cancel_check=task.check_cancelled,
        )

        normalized = orchestrator.last_normalized_output
        if normalized is None:
            raise ExtractionError("Extraction completed without normalized data")

        packaged = package_extraction_result(
            task_id=task.id,
            request=task.request,
            workspace_dir=task.workspace_dir,
            normalized=normalized,
            synthesis_prompt=synthesis.recreation_prompt,
        )
        task.package_path = packaged.package_path
        task.package_filename = packaged.package_filename

        screenshot_path = (
            packaged.normalized_payload.get("target", {}).get("screenshot_path")
            if packaged.normalized_payload.get("mode") == "component"
            else packaged.normalized_payload.get("page_capture", {}).get("screenshot_path")
        )

        task.result = {
            "prompt": packaged.prompt_text,
            "component_tree": synthesis.component_tree.model_dump(),
            "interactions": [interaction.model_dump() for interaction in synthesis.interactions],
            "responsive_rules": [rule.model_dump() for rule in synthesis.responsive_rules],
            "dependencies": [dependency.model_dump() for dependency in synthesis.dependencies],
            "screenshot_path": screenshot_path,
            "screenshot_url": build_task_artifact_url(
                task.id,
                task.workspace_dir,
                screenshot_path,
            ),
            "download_url": f"/api/extract/{task.id}/package",
            "download_filename": task.package_filename,
            "expires_at": None,
            "assets": [
                {
                    **asset,
                    "url": build_task_artifact_url(
                        task.id,
                        task.workspace_dir,
                        asset.get("local_path"),
                    ),
                    "filename": _artifact_filename(asset.get("local_path")),
                }
                for asset in packaged.normalized_payload.get("assets", [])
            ],
            "full_json": packaged.normalized_payload,
        }
        task.completed = True
        await task.emit_progress(12, "complete", "Extraction complete!", done=True)

    except ExtractionError as exc:
        task.error = str(exc)
        await task.emit_progress(0, "error", str(exc), done=True)
    except Exception as exc:
        task.error = str(exc)
        await task.emit_progress(0, "error", f"Unexpected error: {exc}", done=True)


def _artifact_filename(path: str | None) -> str:
    """Return the leaf filename for an artifact path."""
    return Path(path).name if path else ""
