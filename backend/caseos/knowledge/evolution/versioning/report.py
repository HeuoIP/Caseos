"""Knowledge Versioning Report V1 (Sprint 22.4-D, ADR-020).

Renders a Markdown summary of a ``VersionStore`` for one
identity. The report is the **operator-facing audit surface**
of the versioning layer; it does not mutate the store and
does not call any intelligence engine.

Required output (Sprint 22.4-D completion criteria):

    Knowledge Mutation: NOT IMPLEMENTED
    Versioning Foundation: IMPLEMENTED

The two lines are the explicit V1 hard-stop markers. A future
Sprint 22.4.x mutation runtime will keep the second line
("IMPLEMENTED") and change the first to "EXECUTED at
version N".

Architecture boundary (Sprint 22.4-D spec Task 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List

from .object import KnowledgeVersion
from .store import VersionStore


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_version(version: KnowledgeVersion) -> List[str]:
    lines: List[str] = []
    lines.append("### v" + str(version.version_number))
    lines.append("")
    lines.append("- version_id: `" + _safe(version.version_id) + "`")
    lines.append("- proposal_id: `" + _safe(version.proposal_id) + "`")
    lines.append("- created_at: `" + _safe(version.created_at) + "`")
    lines.append("- created_by: `" + _safe(version.created_by) + "`")
    lines.append("- change_reason: " + _safe(version.change_reason))
    if version.previous_version is None:
        lines.append("- previous_version: (initial)")
    else:
        lines.append("- previous_version: `"
                     + str(version.previous_version) + "`")
    lines.append("- snapshot_keys: "
                 + ", ".join("`" + str(k) + "`"
                             for k in sorted(version.snapshot.keys())))
    return lines


def generate_report(
    store: VersionStore,
    identity: str,
    *,
    title: str = "Knowledge Version Report",
) -> str:
    """Render a Markdown report of a ``VersionStore`` for one identity.

    The report is pure over the store. It does not mutate the
    store and does not call any engine.
    """
    history = store.history(identity)
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    lines.append("## Target Identity")
    lines.append("")
    lines.append("- target_identity: `" + _safe(identity) + "`")
    lines.append("- total_versions: " + str(len(history)))
    lines.append("")

    lines.append("## Version History")
    lines.append("")
    if not history:
        lines.append("(no versions for this identity)")
    else:
        for v in history:
            lines.extend(_render_version(v))
            lines.append("")
    lines.append("")

    lines.append("## Status")
    lines.append("")
    lines.append("- Knowledge Mutation: **NOT IMPLEMENTED**")
    lines.append("- Versioning Foundation: **IMPLEMENTED**")
    lines.append("")
    lines.append(
        "  The V1 versioning layer records KnowledgeVersion"
    )
    lines.append(
        "  snapshots in an append-only store and exposes a"
    )
    lines.append(
        "  deterministic differ. It does NOT write to the"
    )
    lines.append(
        "  Knowledge Object, the corpus, the retrieval ranking,"
    )
    lines.append(
        "  the decision engine, the trust engine, or the"
    )
    lines.append(
        "  recommendation engine. The future KO mutation runtime"
    )
    lines.append(
        "  is gated on ADR-020 Rules 1 and 5 and on a concrete"
    )
    lines.append(
        "  Sprint 22.4.x implementation."
    )
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
