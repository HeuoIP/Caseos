"""Human Understanding layer (Sprint 21, ADR-013).

Exports:

    UNKNOWN                -- sentinel for missing information
    HumanContext           -- structured human-understanding object
    HumanValidationResult  -- outcome of validating a HumanContext
    HumanModule            -- pipeline Stage (`human_understanding`)
    extract_human_context  -- pure Project -> HumanContext mapping
    validate_human_context -- pure HumanContext -> ValidationResult
    human_context_to_markdown
    human_context_to_summary

Architecture boundary:

    Human Understanding talks to the *pipeline runtime* only.
    It does NOT import from:
        * caseos.knowledge.retrieval
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.governance
        * caseos.knowledge.intake

    Downstream stages consume `ctx.human_context` (a dict) and
    `ctx.metadata["human_validation"]` (a dict).
"""

from caseos.intelligence.human.object import (
    UNKNOWN,
    HumanContext,
    _is_unknown,
)
from caseos.intelligence.human.extractor import (
    ExtractionResult,
    extract_human_context,
)
from caseos.intelligence.human.validator import (
    HumanValidationResult,
    validate_human_context,
)
from caseos.intelligence.human.report import (
    human_context_to_markdown,
    human_context_to_summary,
)
from caseos.intelligence.human.module import HumanModule

__all__ = [
    "UNKNOWN",
    "HumanContext",
    "HumanValidationResult",
    "HumanModule",
    "ExtractionResult",
    "extract_human_context",
    "validate_human_context",
    "human_context_to_markdown",
    "human_context_to_summary",
    "_is_unknown",
]
