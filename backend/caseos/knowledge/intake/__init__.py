"""Corpus intake layer (Sprint 20.7).

Intake is the stomach of CaseOS. It accepts external information
as RawCaseObject (which is NOT a Knowledge Object), tracks its
lifecycle, and routes it through governance. Nothing reaches the
Knowledge Corpus without passing governance first.

Submodules:

  object     -- RawCaseObject (pre-knowledge container).
  status     -- IntakeStatus lifecycle (NEW -> ... -> ACTIVE).
  manager    -- IntakeManager; the only entry point that knows
                how to move a raw case through the pipeline.
  converter  -- RawCase -> Candidate Knowledge Object.
                Never invents missing ADR-015 fields.
  report     -- Markdown report of the intake state.

Architecture boundary: intake talks to governance only. It does
NOT touch retrieval, decision, trust, or recommendation.

Intake is the stomach.
Governance is the immune system.
Knowledge Object is the memory.
Do not mix them."""

from caseos.knowledge.intake.status import (
    IntakeStatus,
    LIFECYCLE_ORDER,
    is_forward,
)
from caseos.knowledge.intake.object import (
    RawCaseObject,
    new_raw_case,
)
from caseos.knowledge.intake.converter import (
    to_candidate_knowledge_object,
    summarise_candidate,
)
from caseos.knowledge.intake.manager import (
    IntakeManager,
    IntakeError,
    TransitionRecord,
)
from caseos.knowledge.intake.report import (
    generate_report,
)

__all__ = [
    "IntakeStatus",
    "LIFECYCLE_ORDER",
    "is_forward",
    "RawCaseObject",
    "new_raw_case",
    "to_candidate_knowledge_object",
    "summarise_candidate",
    "IntakeManager",
    "IntakeError",
    "TransitionRecord",
    "generate_report",
]
