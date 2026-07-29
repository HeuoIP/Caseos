"""High-level report generator.

ReportGenerator is a thin façade over:

  DecisionEngine.run(vision_json)  ->  DecisionContext
  render_markdown(context)          ->  str

Callers (FastAPI handlers, scripts, tests) only need to depend on this
class. It also handles writing the report to disk if a path is given.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.decision.engine import DecisionEngine
from app.core.recommendation.markdown_generator import render_markdown


@dataclass
class ReportResult:
    markdown: str
    context: Any
    written_to: Path | None = None


class ReportGenerator:
    """Compose DecisionEngine + Markdown renderer into a single call."""

    def __init__(self, engine: DecisionEngine | None = None):
        self.engine = engine or DecisionEngine()

    def generate(
        self,
        vision_json: dict[str, Any],
        output_path: Path | str | None = None,
    ) -> ReportResult:
        """Run the engine and render Markdown. Optionally write to disk."""
        context = self.engine.run(vision_json)
        markdown = render_markdown(context)
        written: Path | None = None
        if output_path is not None:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(markdown, encoding="utf-8")
            written = p
        return ReportResult(markdown=markdown, context=context, written_to=written)


__all__ = ["ReportGenerator", "ReportResult"]