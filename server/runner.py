"""Extraction runner for async pipeline execution."""

import os

from models.errors import ExtractionError
from server.task import ExtractionTask


async def run_extraction(task: ExtractionTask):
    """Execute the extraction pipeline for a task."""
    try:
        # Lazy import to avoid circular dependencies
        from orchestrator import ExtractionOrchestrator

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await task.emit_progress(
                0, "error", "OPENAI_API_KEY not configured", done=True
            )
            return

        # Progress callback wrapper (sync, orchestrator calls it directly)
        def progress_callback(step: int, step_name: str, message: str):
            # Queue the async emit as a task
            import asyncio
            asyncio.create_task(task.emit_progress(step, step_name, message))

        orchestrator = ExtractionOrchestrator(api_key=api_key)

        synthesis = await orchestrator.extract(
            url=task.request.url,
            extraction_mode=task.request.mode,  # Note: orchestrator uses extraction_mode param
            strategy=task.request.strategy,
            query=task.request.query,
            progress_callback=progress_callback,
            cancel_check=task.check_cancelled,
        )

        normalized = orchestrator.last_normalized_output

        task.result = {
            "prompt": synthesis.recreation_prompt,
            "component_tree": synthesis.component_tree.model_dump(),
            "interactions": [i.model_dump() for i in synthesis.interactions],
            "responsive_rules": [r.model_dump() for r in synthesis.responsive_rules],
            "dependencies": [d.model_dump() for d in synthesis.dependencies],
            "screenshot_path": normalized.get_primary_screenshot_path() if normalized else None,
            "assets": [a.model_dump() for a in normalized.assets] if normalized else [],
            "full_json": normalized.model_dump(mode="json") if normalized else {},
        }
        task.completed = True
        await task.emit_progress(12, "complete", "Extraction complete!", done=True)

    except ExtractionError as e:
        task.error = str(e)
        await task.emit_progress(0, "error", str(e), done=True)
    except Exception as e:
        task.error = str(e)
        await task.emit_progress(0, "error", f"Unexpected error: {e}", done=True)
