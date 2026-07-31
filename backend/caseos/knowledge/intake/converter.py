"""RawCaseObject -> Candidate Knowledge Object (Sprint 20.7 spec section 5).

The converter is the ONLY place where a raw case is turned
into something that resembles a Knowledge Object. It is also
the place where the spec rule lives:

    Do NOT auto fill missing ADR-015 fields.
    Missing fields must remain missing.

A candidate KO therefore starts with the same fields every
raw case produces:

    identity      -- a name derived from the title (NOT a
                     full IdentityType-prefixed ADR-015 id;
                     governance assigns the type at promotion)
    situation_context -- None
    observation   -- None
    diagnosis     -- None
    decision      -- None
    principle     -- None
    applicability -- None
    boundary      -- None
    feedback      -- empty list (per ADR-015: required to be present)

What the converter DOES carry over:

    title        -> stored as _raw_title for governance
    source       -> stored as _intake_source
    source_reference -> stored as _intake_reference
    candidate_tags -> stored as _intake_tags
    candidate_identity_type -> stored as _candidate_identity_type

These _intake_* keys are governance metadata, NOT ADR-015
fields. They are consumed by the manager during validation
and removed (or kept as provenance) by the promotion step.

Architecture: the converter never imports retrieval, decision,
trust, or recommendation. It depends only on object.py."""

from __future__ import annotations

import re
from typing import Any

from caseos.knowledge.intake.object import RawCaseObject


_SLUG = re.compile(r"[^a-z0-9_]+")


def _name_from_title(text: str) -> str:
    "Turn a title into a filesystem-safe slug used as the",
    "candidate identity name. Pure Python; no third-party",
    "dependencies. The slug is intentionally short and human",
    "readable; governance is free to rename it during promotion.",
    s = (text or "").strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        s = "unnamed"
    return s
    return s[:80]


def to_candidate_knowledge_object(raw: RawCaseObject) -> dict[str, Any]:
    "Convert a RawCaseObject into a candidate Knowledge Object.",
    "",
    "No ADR-015 field is invented. Every required ADR-015",
    "field is left as None (or empty list, for feedback)",
    "so governance can reject the candidate on its own merits.",
    identity_name = _name_from_title(raw.title)
    identity_block = {
        "name": identity_name,
        "raw_id": raw.id,
    }
    candidate = {
        "identity": identity_block,
        "situation_context": None,
        "observation": None,
        "diagnosis": None,
        "decision": None,
        "principle": None,
        "applicability": None,
        "boundary": None,
        "feedback": [],
        "_intake_source": raw.source,
        "_intake_reference": raw.source_reference,
        "_intake_tags": list(raw.candidate_tags),
        "_candidate_identity_type": raw.candidate_identity_type,
        "_raw_title": raw.title,
        "_raw_description": raw.description,
    }
    return candidate


def summarise_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    "Render a one-row summary of a candidate KO so a human",
    "reviewer can see at a glance what the raw case produced.",
    missing = []
    for f in (
        "situation_context", "observation", "diagnosis",
        "decision", "principle",
        "applicability", "boundary",
    ):
        if candidate.get(f) is None:
            missing.append(f)
    identity_block = candidate.get("identity") or {}
    return {
        "identity_name": identity_block.get("name"),
        "missing_fields": missing,
        "candidate_identity_type_hint": candidate.get("_candidate_identity_type"),
    }


__all__ = ["to_candidate_knowledge_object", "summarise_candidate"]
