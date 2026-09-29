"""Admission vs Evolution semantic boundary (Sprint 25.3-A).

This module makes the boundary between **Admission** and
**Evolution** explicit. It is a pure-data / pure-function
module; it owns:

    * ``ADMISSION_OWNED_VERSIONS``      -- tuple of versions
                                           Admission is allowed
                                           to target (V1: only 1)
    * ``EVOLUTION_OWNED_MIN_VERSION``   -- the smallest version
                                           Evolution is allowed
                                           to touch (V1: 2)
    * ``SEMANTIC_BOUNDARY_TABLE``       -- a frozen table of
                                           "what each layer does
                                           for each version"
    * ``is_admission_owned_version``    -- predicate
    * ``is_evolution_owned_version``    -- predicate

No I/O, no mutation, no side effects. The intent is to give
future Writer / Evolution Sprints a single, testable source
of truth for the "who owns what version" rule.

Why this lives here
-------------------

    The Admission / Evolution split is a *contract* concern,
    not an implementation concern. By placing the boundary
    constants in the ingestion package (where Admission
    itself lives), we keep them close to the data that
    enforces them. The Evolution package will, in turn,
    be expected to read from this boundary module -- but
    only via import (the boundary is *consulted*, not
    *owned*, by Evolution).

The boundary module imports nothing from the Evolution
package; it is the canonical authority.
"""
from __future__ import annotations

from typing import Tuple


# ---------------------------------------------------------------------------
# Version ownership constants
# ---------------------------------------------------------------------------


# V1 Admission is single-version. A future Sprint may extend
# Admission to also support "re-admission of a withdrawn
# record" or similar, but V1 is strict: only the first
# version of a KnowledgeObject is owned by Admission.
ADMISSION_OWNED_VERSIONS: Tuple[int, ...] = (1,)


# V1 Evolution owns everything from version 2 upwards. The
# Evolution package (Sprint 22.4 series) is the canonical
# owner of every subsequent version of an existing KO.
EVOLUTION_OWNED_MIN_VERSION: int = 2


# ---------------------------------------------------------------------------
# Semantic boundary table
# ---------------------------------------------------------------------------


SEMANTIC_BOUNDARY_TABLE: Tuple[Tuple[str, str, str], ...] = (
    (
        "v1",
        "Admission (Sprint 25.3-A)",
        "First entry. Eligibility already cleared by Promotion "
        "(Sprint 25.2-A). AdmissionChecker signs the immutable "
        "AdmissionCandidate handoff. A future Writer Sprint "
        "(25.4+) registers the KO and seeds VersionStore with "
        "version 1.",
    ),
    (
        "v2+",
        "Evolution (Sprint 22.4 series)",
        "Subsequent updates. Owned by EvolutionTransaction / "
        "GovernanceGate / VersionStore (Sprint 22.4-A through "
        "22.4-H). Admission does NOT touch v2+.",
    ),
    (
        "rollback",
        "Evolution (Sprint 22.4-G)",
        "Rollback is an Evolution concern, not an Admission "
        "concern. A rollback restores a previous version; it "
        "does not create a new first entry.",
    ),
)


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def is_admission_owned_version(version: int) -> bool:
    """True iff ``version`` is a version Admission is allowed
    to target under the current V1 contract."""
    if not isinstance(version, int):
        return False
    return version in ADMISSION_OWNED_VERSIONS


def is_evolution_owned_version(version: int) -> bool:
    """True iff ``version`` is a version Evolution owns
    (i.e. greater than or equal to ``EVOLUTION_OWNED_MIN_VERSION``)."""
    if not isinstance(version, int):
        return False
    return version >= EVOLUTION_OWNED_MIN_VERSION


def ownership_of(version: int) -> str:
    """Return the layer name that owns ``version``.

    Returns ``"admission"``, ``"evolution"``, or ``"unknown"``
    for malformed inputs.
    """
    if not isinstance(version, int):
        return "unknown"
    if is_admission_owned_version(version):
        return "admission"
    if is_evolution_owned_version(version):
        return "evolution"
    return "unknown"
