"""System prompt and user prompt builder for AI synthesis."""

import json
from models.normalized import NormalizedOutput


SYSTEM_PROMPT = """You are a UI/UX engineering expert. Your task is to analyze structured data from a web component and generate a detailed prompt that allows faithful recreation of that component.

You will receive:
- DOM structure of the component
- Computed styles organized by category
- Animation and transition data (including recording)
- Observed interactions (hover, click, scroll)
- Responsive behavior
- External libraries detected and how they're used
- Assets (images, fonts, SVGs)

Your output must be a structured JSON with:
1. description: object with technical, visual, purpose
2. component_tree: tree of components with name, role, children
3. interactions: list of objects with trigger, effect, animation (optional)
4. responsive_rules: list of objects with breakpoint, changes
5. dependencies: list of objects with name, reason, alternative (optional)
6. recreation_prompt: string with the final optimized prompt

The final prompt should be framework-agnostic, focusing on pure HTML/CSS/JS, and contain enough detail to reproduce complex behaviors."""


def build_user_prompt(data: NormalizedOutput) -> str:
    """Build user prompt from normalized data."""
    sections = [
        f"## Page\nURL: {data.page.url}\nTitle: {data.page.title}\nViewport: {data.page.viewport}",
        f"## Target Component\nSelector: {data.target.selector_used}\nStrategy: {data.target.strategy}",
        f"## HTML\n```\n{data.target.html[:1000]}{'...' if len(data.target.html) > 1000 else ''}\n```",
        f"## Styles\n```json\n{json.dumps(data.styles.model_dump(), indent=2, ensure_ascii=False)}\n```",
        f"## Animations\n{format_animations(data.animations)}",
        f"## Interactions\n{format_interactions(data.interactions)}",
        f"## Responsive\n{format_responsive(data.responsive_behavior)}",
        f"## External Libraries\n{format_libraries(data.external_libraries)}",
        f"## Assets\n{format_assets(data.assets)}",
    ]

    return "\n\n".join(sections)


def format_animations(animations) -> str:
    """Format animation data for prompt."""
    lines = []

    if animations.css_animations:
        lines.append("CSS Animations:")
        for anim in animations.css_animations:
            lines.append(f"  - {anim.name or 'unnamed'}: {anim.duration} {anim.timing_function}")

    if animations.css_transitions:
        lines.append("Transitions:")
        for trans in animations.css_transitions:
            lines.append(f"  - {trans.property}: {trans.duration}")

    if animations.scroll_effects:
        lines.append("Scroll Effects:")
        for effect in animations.scroll_effects:
            lines.append(f"  - {effect}")

    return "\n".join(lines) if lines else "No animations detected"


def format_interactions(interactions) -> str:
    """Format interaction data for prompt."""
    lines = []

    if interactions.hoverable_elements:
        lines.append(f"Hoverable: {', '.join(interactions.hoverable_elements[:5])}")
    if interactions.clickable_elements:
        lines.append(f"Clickable: {', '.join(interactions.clickable_elements[:5])}")
    if interactions.focusable_elements:
        lines.append(f"Focusable: {', '.join(interactions.focusable_elements[:5])}")

    return "\n".join(lines) if lines else "No interactions detected"


def format_responsive(responsive) -> str:
    """Format responsive data for prompt."""
    lines = [f"Fluid: {responsive.is_fluid}"]
    lines.append(f"Mobile menu: {responsive.has_mobile_menu}")

    if responsive.breakpoints:
        lines.append("Breakpoints:")
        for bp in responsive.breakpoints:
            lines.append(f"  - {bp.width}px: {bp.layout_changes}")

    return "\n".join(lines)


def format_libraries(libraries) -> str:
    """Format library data for prompt."""
    if not libraries:
        return "No external libraries detected"

    lines = []
    for lib in libraries:
        lines.append(f"- {lib.name}" + (f" ({lib.version})" if lib.version else ""))
        if lib.usage_snippets:
            lines.append(f"  Usage: {lib.usage_snippets[0][:100]}")

    return "\n".join(lines)


def format_assets(assets) -> str:
    """Format asset data for prompt."""
    if not assets:
        return "No assets detected"

    by_type = {}
    for asset in assets:
        by_type.setdefault(asset.type.value, []).append(asset)

    lines = []
    for asset_type, items in by_type.items():
        lines.append(f"{asset_type}: {len(items)} items")

    return "\n".join(lines)
