"""Public recommendation-package exports."""

from app.core.recommendation.markdown_generator import render_markdown
from app.core.recommendation.report_generator import ReportGenerator, ReportResult

__all__ = ["ReportGenerator", "ReportResult", "render_markdown"]