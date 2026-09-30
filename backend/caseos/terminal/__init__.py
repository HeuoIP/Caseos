"""Terminal MVP V1 (Sprint 26.0-A).

This package is the **product entry point** for CaseOS Knowledge
Foundation V1. It exposes a single, immutable, deterministic
flow that turns a partial-information user request into a
ranked list of similar Knowledge Objects from the existing
retrieval stack:

    TerminalRequest
          |
          v
        Validator
          |
          v
        QueryBuilder
          |
          v
        RetrievalPipeline
          |
          v
        TerminalResult

Terminal V1 does NOT generate images, does NOT call any AI
runtime, does NOT mutate the corpus. It only orchestrates the
existing retrieval layer.

Architecture boundary (Sprint 26.0-A spec section 7):

    This package may import from:
        * caseos.knowledge.retrieval.pipeline
        * caseos.knowledge.retrieval.object
        * caseos.knowledge.object
        * stdlib

    This package must NOT import from:
        * caseos.intelligence.*
        * caseos.brain.*
        * caseos.knowledge.evolution.*
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.knowledge.intake
        * caseos.knowledge.corpus
        * any LLM / VLM / embedding SDK
"""
from .object import (
    TerminalQuery,
    TerminalRequest,
    TerminalResult,
    TerminalValidationResult,
)
from .contract import (
    DEFAULT_LIMIT,
    DEFAULT_TERMINAL_CONTRACT,
    MAX_LIMIT,
    MIN_LIMIT,
    RULE_LABELS,
    TerminalContract,
    default_contract,
)
from .validator import (
    TerminalValidator,
    TerminalValidatorError,
)
from .query_builder import (
    TerminalQueryBuilder,
    TerminalQueryBuilderError,
)
from .service import (
    TerminalService,
    TerminalServiceError,
)

__all__ = [
    # Object
    "TerminalRequest",
    "TerminalQuery",
    "TerminalResult",
    "TerminalValidationResult",
    # Contract
    "TerminalContract",
    "DEFAULT_TERMINAL_CONTRACT",
    "default_contract",
    "DEFAULT_LIMIT",
    "MIN_LIMIT",
    "MAX_LIMIT",
    "RULE_LABELS",
    # Validator
    "TerminalValidator",
    "TerminalValidatorError",
    # Query Builder
    "TerminalQueryBuilder",
    "TerminalQueryBuilderError",
    # Service
    "TerminalService",
    "TerminalServiceError",
]
