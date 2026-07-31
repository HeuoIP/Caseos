"""Deterministic duplicate-candidate detection for Knowledge Objects.

Per Sprint 20.6 spec section 3, this module answers the question:

  Are these two KOs likely the same knowledge, expressed twice?

We do NOT use embeddings, vector similarity, or LLM calls. The
detection is deterministic and inspectable, based on:

  1. Same IdentityType prefix (GoldenCase, DecisionPattern, ...).
  2. Same name part of the identity (short_id after the dot).
  3. Overlapping situation_context keywords.
  4. Overlapping decision keywords.

The output is a list of DuplicateCandidate records. A non-empty
result means the corpus has two competing versions of the same
underlying knowledge; governance must resolve them before they
both enter the retrieval pool.

Architecture boundary: this module is read-only. It never deletes
or merges KOs. The Promotion module (promotion.py) is the place
where lifecycle transitions happen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Decision keywords (verbs) used to compare the Decision field of
# two KOs. They are intentionally generic so the matcher works on
# both short and long decision strings.
DECISION_KEYWORDS = (
    "create", "build", "add", "remove",
    "replace", "consolidate", "anchor",
    "open", "close", "extend", "connect",
    "remove_before_add", "narrative",
)

# Threshold for decision keyword overlap: at least this many
# keywords must appear in both KOs to flag a candidate.
DECISION_OVERLAP_THRESHOLD = 1


def _identity_type(identity: str) -> str:
    return identity.split(".", 1)[0] if "." in identity else ""


def _identity_name(identity: str) -> str:
    return identity.split(".", 1)[1] if "." in identity else identity


def _keywords_from_situation(ko: dict) -> set[str]:
    "Pull free-form keywords out of situation_context.",
    "Accepts a dict or a string (per ADR-015 spec).",
    ctx = ko.get("situation_context")
    out: set[str] = set()
    if isinstance(ctx, dict):
        for value in ctx.values():
            if isinstance(value, str):
                for token in value.lower().replace(",", " ").split():
                    if len(token) > 2:
                        out.add(token)
    elif isinstance(ctx, str):
        for token in ctx.lower().replace(",", " ").split():
            if len(token) > 2:
                out.add(token)
    return out


def _keywords_from_decision(ko: dict) -> set[str]:
    "Pull the decision verbs that are in DECISION_KEYWORDS.",
    decision = ko.get("decision")
    if isinstance(decision, dict):
        text = " ".join(
            str(v) for v in decision.values() if isinstance(v, str)
        )
    elif isinstance(decision, str):
        text = decision
    else:
        text = ""
    text = text.lower()
    return {kw for kw in DECISION_KEYWORDS if kw in text}


def _situation_overlap(a: set[str], b: set[str]) -> set[str]:
    return a & b


@dataclass
class DuplicateCandidate:
    "One pair of KOs that the deterministic matcher flagged",
    "as carrying the same underlying knowledge. The report",
    "renders these so a human can decide which to keep.",

    object_a: str  # identity of object A
    object_b: str  # identity of object B
    reason: str    # human-readable explanation
    similarity_basis: list[str]  # which signals fired

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_a": self.object_a,
            "object_b": self.object_b,
            "reason": self.reason,
            "similarity_basis": list(self.similarity_basis),
        }


def _same_type_and_name(a: dict, b: dict) -> bool:
    return (
        _identity_type(str(a.get("identity"))) ==
        _identity_type(str(b.get("identity")))
    ) and (
        _identity_name(str(a.get("identity"))) ==
        _identity_name(str(b.get("identity")))
    )


def _compare(a: dict, b: dict) -> tuple[bool, list[str], str]:
    "Compare two KOs; return (is_duplicate, basis, reason).",
    basis: list[str] = []
    type_a = _identity_type(str(a.get("identity")))
    name_a = _identity_name(str(a.get("identity")))
    type_b = _identity_type(str(b.get("identity")))
    name_b = _identity_name(str(b.get("identity")))

    if type_a == type_b and type_a:
        basis.append("same-identity-type")
    if name_a == name_b and name_a:
        basis.append("same-identity-name")
    if _same_type_and_name(a, b):
        # exact identity match is always a duplicate signal
        basis.append("identity-collision")

    sit_a = _keywords_from_situation(a)
    sit_b = _keywords_from_situation(b)
    sit_overlap = sit_a & sit_b
    if sit_overlap:
        basis.append("situation-keyword-overlap")

    dec_a = _keywords_from_decision(a)
    dec_b = _keywords_from_decision(b)
    dec_overlap = dec_a & dec_b
    if len(dec_overlap) >= DECISION_OVERLAP_THRESHOLD:
        basis.append("decision-keyword-overlap")

    # Duplicate verdict: at least one of the strong signals fired.
    strong = (
        "identity-collision" in basis
        or len(sit_overlap) >= 2
        or (len(sit_overlap) >= 1 and len(dec_overlap) >= DECISION_OVERLAP_THRESHOLD)
    )
    if not strong:
        return False, [], ""

    reason_parts: list[str] = []
    if "identity-collision" in basis:
        reason_parts.append("identical identity name")
    if sit_overlap:
        sample = sorted(sit_overlap)[:3]
        reason_parts.append("shared situation: " + ", ".join(sample))
    if dec_overlap:
        reason_parts.append("shared decision verbs: " + ", ".join(sorted(dec_overlap)))
    reason = "; ".join(reason_parts)
    return True, basis, reason


def detect_duplicates(kos: list[dict]) -> list[DuplicateCandidate]:
    "Return all duplicate candidate pairs from a corpus.",
    "",
    "Each KO appears at most once as object_a; the list is",
    "sorted by object_a then object_b for deterministic output.",
    out: list[DuplicateCandidate] = []
    n = len(kos)
    for i in range(n):
        a = kos[i]
        ident_a = str(a.get("identity"))
        for j in range(i + 1, n):
            b = kos[j]
            ident_b = str(b.get("identity"))
            if ident_a == ident_b:
                # Self or literal duplicate identity string -- collapse.
                out.append(DuplicateCandidate(
                    object_a=ident_a,
                    object_b=ident_b,
                    reason="identical identity string",
                    similarity_basis=["identity-collision"],
                ))
                continue
            is_dup, basis, reason = _compare(a, b)
            if is_dup:
                out.append(DuplicateCandidate(
                    object_a=ident_a,
                    object_b=ident_b,
                    reason=reason,
                    similarity_basis=basis,
                ))
    return out


def summarize(candidates: list[DuplicateCandidate]) -> dict[str, int]:
    "Count how many times each basis fired across all candidates.",
    out: dict[str, int] = {}
    for c in candidates:
        for b in c.similarity_basis:
            out[b] = out.get(b, 0) + 1
    return out


__all__ = [
    "DuplicateCandidate",
    "detect_duplicates",
    "summarize",
]
