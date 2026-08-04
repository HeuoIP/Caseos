"""Evolution Change Type Enum (Sprint 22.4-I, ADR-020).

Sprint 22.4-I unifies the change_type contract across the
evolution pipeline. Prior to this sprint the Mutation
layer used ``_candidate``-suffixed names (e.g.
``boundary_update_candidate``) while every upstream layer
(ChangeIntent, EvolutionTransaction, Governance Gate) used
bare names (e.g. ``boundary_update``). The misalignment
prevented real pipeline data from reaching the Mutation
runtime.

This module defines the single canonical taxonomy. All
values are bare strings. The Mutation layer's allow-list,
the Governance allow-list, and the ChangeIntent schema
all reference this enum.

V1 allowed members:

    EvolutionChangeType.BOUNDARY_UPDATE       = "boundary_update"
    EvolutionChangeType.PRINCIPLE_UPDATE      = "principle_update"
    EvolutionChangeType.APPLICABILITY_UPDATE  = "applicability_update"

Forbidden change types (used by the Governance Gate as a
named rejection vocabulary) are **not** enum members; they
remain string literals in ``evolution/policy.py`` because
they describe rejection rules, not allowed evolution
taxonomy values.

Architecture boundary (Sprint 22.4-I spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * stdlib
"""
from __future__ import annotations

from enum import Enum


class EvolutionChangeType(Enum):
    """The unified evolution change_type taxonomy.

    Members are intentionally lowercase strings so they
    round-trip through JSON without further encoding.
    """

    BOUNDARY_UPDATE = "boundary_update"
    PRINCIPLE_UPDATE = "principle_update"
    APPLICABILITY_UPDATE = "applicability_update"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


__all__ = ["EvolutionChangeType"]
