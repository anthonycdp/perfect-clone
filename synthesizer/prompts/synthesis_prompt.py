"""System prompt and user prompt builder for AI synthesis."""

import json

from models.extraction import ExtractionMode
from models.normalized import FullPageNormalizedOutput, NormalizedOutput


SYSTEM_PROMPT = """You are a UI/UX engineering expert. Your task is to analyze structured data from either a web component or an entire landing page and generate a detailed prompt that allows faithful recreation.

You will receive:
- DOM structure from the rendered extraction scope
- Computed styles organized by category
- A screenshot of the extracted component or page when available
- Animation and transition data (including recording)
- A structured runtime scroll probe when scroll-linked effects were observed
- Observed interactions (hover, click, scroll)
- Responsive behavior
- External libraries detected and how they're used
- Assets (images, fonts, SVGs)
- For full-page extractions, a section-by-section breakdown with screenshots, runtime motion evidence, and rich-media captures when available
- The final deliverable will be bundled with a local package that contains prompt.txt, README.md, manifest.json, normalized.json, a primary screenshot when available, and supporting artifact folders
- When both a promoted primary screenshot and an element_screenshot exist, the primary screenshot is the visual source of truth and the element_screenshot is only a structural scope reference

Your output must be a structured JSON with:
1. description: object with technical, visual, purpose
2. component_tree: tree of components with name, role, children
3. interactions: list of objects with trigger, effect, animation (optional)
4. responsive_rules: list of objects with breakpoint, changes
5. dependencies: list of objects with name, reason, alternative (optional)
6. recreation_prompt: string with the final optimized prompt

The final prompt should be framework-agnostic, focus on pure HTML/CSS/JS, and contain enough detail to reproduce complex behaviors.
The recreation_prompt must explicitly instruct the next AI or developer to inspect the package files before coding.
Do not claim that you directly inspected packaged files beyond the structured data and screenshot provided in this request."""


def build_user_prompt(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Build a user prompt from normalized extraction data."""
    if data.mode == ExtractionMode.FULL_PAGE:
        return _build_full_page_prompt(data)
    return _build_component_prompt(data)


def _build_component_prompt(data: NormalizedOutput) -> str:
    """Build the component-oriented prompt."""
    sections = [
        format_page_info(data),
        format_package_context(),
        (
            "## Target Component\n"
            f"Selector: {data.target.selector_used}\n"
            f"Strategy: {data.target.strategy}\n"
            f"Bounding Box: {data.target.bounding_box.model_dump(mode='json')}\n"
            f"Frame URL: {data.target.frame_url or data.page.url}\n"
            f"Frame Name: {data.target.frame_name or 'n/a'}\n"
            f"Same Origin Accessible: {data.target.same_origin_accessible}\n"
            f"Within Shadow DOM: {data.target.within_shadow_dom}"
        ),
        format_visual_reference(data),
        format_frame_limitations(data),
        format_collection_limitations(data),
        _format_html_block("## HTML", data.target.html, limit=1_200),
        format_styles(data),
        format_animations(data),
        format_scroll_probe(data),
        format_interactions(data),
        format_responsive(data),
        format_libraries(data),
        format_assets(data),
        format_rich_media(data),
    ]
    return "\n\n".join(sections)


def _build_full_page_prompt(data: FullPageNormalizedOutput) -> str:
    """Build the full-page prompt."""
    sections = [
        format_page_info(data),
        format_package_context(),
        (
            "## Landing Page Capture\n"
            f"Scroll Completed: {data.page_capture.scroll_completed}\n"
            f"Canvas Bounds: {data.page_capture.bounding_box.model_dump(mode='json')}\n"
            f"Detected Sections: {len(data.page_capture.sections)}"
        ),
        format_page_sections(data.page_capture.sections),
        format_collection_limitations(data),
        _format_html_block("## Page HTML", data.page_capture.html, limit=2_000),
        format_styles(data),
        format_animations(data),
        format_scroll_probe(data),
        format_interactions(data),
        format_responsive(data),
        format_libraries(data),
        format_assets(data),
        format_rich_media(data),
    ]
    return "\n\n".join(sections)


def format_page_info(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format page metadata."""
    return (
        "## Page\n"
        f"Mode: {data.mode.value}\n"
        f"URL: {data.page.url}\n"
        f"Title: {data.page.title}\n"
        f"Viewport: {data.page.viewport}"
    )


def format_package_context() -> str:
    """Describe the packaged files that will ship with the final prompt."""
    return (
        "## Package Context\n"
        "The final delivery will include `prompt.txt`, `README.md`, `manifest.json`, "
        "`normalized.json`, a primary screenshot when available, a `sections/` folder "
        "with per-section artifacts, and supporting folders such as `assets/`, `rich_media/`, "
        "`animations/`, and `animations/scroll_probe/`.\n"
        "When both a primary screenshot and an `element_screenshot` exist, treat the primary "
        "screenshot as the visual truth and use the element screenshot only to confirm scope.\n"
        "Write the recreation prompt so the next AI or developer inspects those files "
        "before building."
    )


def format_visual_reference(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Describe which image should drive the final visual recreation."""
    if data.mode != ExtractionMode.COMPONENT:
        return ""

    visual_reference = data.target.visual_reference
    lines = ["## Visual Reference"]
    lines.append(f"Primary Screenshot: {data.target.screenshot_path or 'n/a'}")
    if data.target.element_screenshot_path:
        lines.append(
            f"Element Screenshot: {data.target.element_screenshot_path}"
        )
    if visual_reference.promoted:
        lines.append("Promoted: True")
        lines.append(
            "Primary screenshot was promoted from the scroll probe because the "
            "component depends on runtime visuals."
        )
        if visual_reference.source_path:
            lines.append(f"Promoted From: {visual_reference.source_path}")
        if visual_reference.reason:
            lines.append(f"Reason: {visual_reference.reason}")
        lines.append(
            "If the element screenshot disagrees with the primary screenshot, prioritize "
            "the primary screenshot, `manifest.json`, `normalized.json`, and the scroll probe artifacts."
        )
    else:
        lines.append("Promoted: False")
        lines.append(
            "Use the primary screenshot as the main visual reference for the component."
        )

    return "\n".join(lines)


def format_page_sections(sections) -> str:
    """Format detected landing page sections."""
    if not sections:
        return "## Sections\nNo major sections detected"

    lines = ["## Sections"]
    for section in sections:
        lines.append(
            f"### {section.section_id or section.name or 'section'}"
        )
        lines.append(f"Name: {section.name}")
        lines.append(f"Selector: `{section.selector}`")
        lines.append(f"Tag: {section.tag}")
        lines.append(f"Bounds: {section.bounding_box.model_dump(mode='json')}")
        lines.append(f"Excerpt: {section.text_excerpt or 'n/a'}")
        if section.screenshot_path:
            lines.append(f"Screenshot: {section.screenshot_path}")
        if section.html:
            html_snippet = " ".join(section.html.split())[:500]
            suffix = "..." if len(section.html) > 500 else ""
            lines.append(f"HTML Snippet: `{html_snippet}{suffix}`")
        if section.interactions:
            interaction_bits: list[str] = []
            if section.interactions.hoverable_elements:
                interaction_bits.append(
                    "hoverable="
                    + ", ".join(section.interactions.hoverable_elements[:4])
                )
            if section.interactions.clickable_elements:
                interaction_bits.append(
                    "clickable="
                    + ", ".join(section.interactions.clickable_elements[:4])
                )
            if section.interactions.scroll_containers:
                interaction_bits.append(
                    "scroll="
                    + ", ".join(section.interactions.scroll_containers[:3])
                )
            if interaction_bits:
                lines.append("Interactions: " + " | ".join(interaction_bits))
        if section.animations:
            if section.animations.scroll_effects:
                lines.append(
                    "Scroll Effects: " + " | ".join(section.animations.scroll_effects[:4])
                )
            if (
                section.animations.scroll_probe
                and section.animations.scroll_probe.observations
            ):
                lines.append(
                    "Scroll Probe: "
                    + " | ".join(section.animations.scroll_probe.observations[:3])
                )
            if (
                section.animations.scroll_probe
                and section.animations.scroll_probe.frames_dir
            ):
                lines.append(
                    f"Scroll Probe Frames: {section.animations.scroll_probe.frames_dir}"
                )
            if (
                section.animations.scroll_probe
                and section.animations.scroll_probe.video_path
            ):
                lines.append(
                    f"Scroll Probe Video: {section.animations.scroll_probe.video_path}"
                )
        if section.rich_media:
            media_bits = []
            for media in section.rich_media[:4]:
                media_bits.append(f"{media.type.value} via `{media.selector}`")
            lines.append("Rich Media: " + " | ".join(media_bits))
        if section.collection_limitations:
            lines.append(
                "Limitations: " + " | ".join(section.collection_limitations[:3])
            )
    return "\n".join(lines)


def format_frame_limitations(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format any frame-specific limitations for component prompts."""
    if data.mode != ExtractionMode.COMPONENT:
        return ""

    if not data.target.frame_limitations:
        return "## Frame Limitations\nNone"

    lines = ["## Frame Limitations"]
    for limitation in data.target.frame_limitations:
        lines.append(f"- {limitation}")
    return "\n".join(lines)


def format_styles(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format style summary."""
    return (
        "## Styles\n"
        f"```json\n{json.dumps(data.styles.model_dump(), indent=2, ensure_ascii=False)}\n```"
    )


def format_collection_limitations(
    data: NormalizedOutput | FullPageNormalizedOutput,
) -> str:
    """Format extraction limitations that affect the final fidelity."""
    if not data.collection_limitations:
        return "## Collection Limitations\nNone"

    lines = ["## Collection Limitations"]
    for limitation in data.collection_limitations:
        lines.append(f"- {limitation}")
    return "\n".join(lines)


def format_animations(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format animation data for prompt."""
    lines = ["## Animations"]

    if data.animations.css_animations:
        lines.append("CSS Animations:")
        for anim in data.animations.css_animations:
            lines.append(
                f"  - {anim.name or 'unnamed'}: {anim.duration} {anim.timing_function}"
            )

    if data.animations.css_transitions:
        lines.append("Transitions:")
        for trans in data.animations.css_transitions:
            lines.append(f"  - {trans.property}: {trans.duration}")

    if data.animations.scroll_effects:
        lines.append("Scroll Effects:")
        for effect in data.animations.scroll_effects:
            lines.append(f"  - {effect}")

    if len(lines) == 1:
        lines.append("No animations detected")

    return "\n".join(lines)


def format_scroll_probe(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format runtime scroll probe output for prompt generation."""
    scroll_probe = data.animations.scroll_probe
    if scroll_probe is None:
        return "## Scroll Probe\nNo runtime scroll probe was captured"

    lines = [
        "## Scroll Probe",
        f"Context: {scroll_probe.context}",
        f"Triggered: {scroll_probe.triggered}",
        f"Range: {round(scroll_probe.range_start, 2)} -> {round(scroll_probe.range_end, 2)}",
        f"Steps: {scroll_probe.step_count}",
        f"FPS: {scroll_probe.fps}",
    ]

    if scroll_probe.tracked_selectors:
        lines.append(
            "Tracked Selectors: "
            + ", ".join(
                "target root" if selector == "__target__" else f"`{selector}`"
                for selector in scroll_probe.tracked_selectors
            )
        )
    if scroll_probe.overlay_selectors:
        lines.append(
            "Overlay Selectors: "
            + ", ".join(f"`{selector}`" for selector in scroll_probe.overlay_selectors)
        )
    if scroll_probe.frames_dir:
        lines.append(f"Frames Dir: {scroll_probe.frames_dir}")
    if scroll_probe.video_path:
        lines.append(f"Video Path: {scroll_probe.video_path}")
    if scroll_probe.key_frames:
        lines.append(f"Key Frames: {scroll_probe.key_frames}")

    if scroll_probe.observations:
        lines.append("Observations:")
        for observation in scroll_probe.observations:
            lines.append(f"  - {observation}")

    if scroll_probe.state_changes:
        lines.append("State Changes:")
        for change in scroll_probe.state_changes[:8]:
            pretty_selector = (
                "target root" if change.selector == "__target__" else f"`{change.selector}`"
            )
            lines.append(
                f"  - {pretty_selector}: {', '.join(change.property_changes.keys())}"
            )

    if scroll_probe.limitations:
        lines.append("Limitations:")
        for limitation in scroll_probe.limitations:
            lines.append(f"  - {limitation}")

    return "\n".join(lines)


def format_interactions(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format interaction data for prompt."""
    lines = ["## Interactions"]

    if data.interactions.hoverable_elements:
        lines.append(f"Hoverable: {', '.join(data.interactions.hoverable_elements[:8])}")
    if data.interactions.clickable_elements:
        lines.append(f"Clickable: {', '.join(data.interactions.clickable_elements[:8])}")
    if data.interactions.focusable_elements:
        lines.append(f"Focusable: {', '.join(data.interactions.focusable_elements[:8])}")
    if data.interactions.scroll_containers:
        lines.append(
            f"Scroll Containers: {', '.join(data.interactions.scroll_containers[:5])}"
        )

    if len(lines) == 1:
        lines.append("No interactions detected")

    return "\n".join(lines)


def format_responsive(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format responsive data for prompt."""
    lines = ["## Responsive"]
    lines.append(f"Fluid: {data.responsive_behavior.is_fluid}")
    lines.append(f"Mobile menu: {data.responsive_behavior.has_mobile_menu}")

    if data.responsive_behavior.breakpoints:
        lines.append("Breakpoints:")
        for bp in data.responsive_behavior.breakpoints:
            lines.append(f"  - {bp.width}px: {bp.layout_changes}")

    return "\n".join(lines)


def format_libraries(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format library data for prompt."""
    if not data.external_libraries:
        return "## External Libraries\nNo external libraries detected"

    lines = ["## External Libraries"]
    for library in data.external_libraries:
        lines.append(
            f"- {library.name}" + (f" ({library.version})" if library.version else "")
        )
        if library.usage_snippets:
            lines.append(f"  Usage: {library.usage_snippets[0][:100]}")

    return "\n".join(lines)


def format_assets(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format asset summary for prompt."""
    if not data.assets:
        return "## Assets\nNo assets detected"

    by_type: dict[str, int] = {}
    for asset in data.assets:
        by_type.setdefault(asset.type.value, 0)
        by_type[asset.type.value] += 1

    lines = ["## Assets"]
    for asset_type, count in by_type.items():
        lines.append(f"- {asset_type}: {count} items")
    return "\n".join(lines)


def format_rich_media(data: NormalizedOutput | FullPageNormalizedOutput) -> str:
    """Format runtime media captures for the synthesis prompt."""
    if not data.rich_media:
        return "## Rich Media\nNo canvas, video, or WebGL media captured"

    lines = ["## Rich Media"]
    for media in data.rich_media:
        source_summary = f" sources={len(media.source_urls)}" if media.source_urls else ""
        poster_summary = f" poster={media.poster_url}" if media.poster_url else ""
        flags = (
            ", ".join(
                name for name, enabled in media.playback_flags.items() if enabled
            )
            if media.playback_flags
            else ""
        )
        lines.append(
            f"- {media.type.value} via `{media.selector}`{source_summary}{poster_summary}"
        )
        if media.document_level:
            lines.append("  Scope: document-level overlay outside the component subtree")
        if media.linked_selectors:
            lines.append(
                "  Linked Selectors: "
                + ", ".join(f"`{selector}`" for selector in media.linked_selectors)
            )
        if media.effect_summary:
            lines.append(f"  Effect: {media.effect_summary}")
        if media.snapshot_path:
            lines.append(f"  Snapshot: {media.snapshot_path}")
        if flags:
            lines.append(f"  Playback Flags: {flags}")
        for limitation in media.limitations:
            lines.append(f"  Limitation: {limitation}")

    return "\n".join(lines)


def _format_html_block(title: str, html: str, limit: int) -> str:
    """Format HTML as a fenced block with a size cap."""
    snippet = html[:limit]
    suffix = "..." if len(html) > limit else ""
    return f"{title}\n```\n{snippet}{suffix}\n```"
