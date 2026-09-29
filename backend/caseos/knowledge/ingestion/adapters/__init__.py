"""Ingestion adapters (Sprint 25.1-A inferred).

This subpackage is the **only** place inside ``ingestion``
that may import from sibling layers (e.g. ``caseos.knowledge.intake``).
The core contract layer (``object``, ``contract``,
``validator``, ``report``) remains pure schema with no
dependency on raw data sources.

Boundary rules
--------------

    * The four core modules do NOT import from
      ``caseos.knowledge.intake`` (verified by AST tests).
    * Adapters MAY import from
      ``caseos.knowledge.intake`` because their job is
      to translate raw input into ``CaseKnowledge``.
    * Adapters MUST NOT mutate the source object.
    * Adapters MUST NOT pull intelligence, retrieval,
      evolution, governance, or brain modules into the
      ingestion boundary.
"""
from .intake_adapter import (
    DEFAULT_INTAKE_ADAPTER,
    IntakeAdapter,
    IntakeAdapterError,
    RawIntakeRecord,
    adapt_raw_case,
    adapt_raw_cases,
)

__all__ = [
    "IntakeAdapter",
    "IntakeAdapterError",
    "RawIntakeRecord",
    "DEFAULT_INTAKE_ADAPTER",
    "adapt_raw_case",
    "adapt_raw_cases",
]
