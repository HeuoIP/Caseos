"""Evolution Audit Log Report V1 (Sprint 22.4-E, ADR-020 Rule 3).

Renders a Markdown summary of an ``AuditStore`` for one
target_identity. The report is the **operator-facing audit
surface** of the V2 audit layer; it does not mutate the
store and does not call any intelligence engine.

Required status markers (Sprint 22.4-E completion criteria):

    Audit Schema Foundation:  IMPLEMENTED
    Knowledge Mutation:        NOT IMPLEMENTED

The two lines are the explicit V1 hard-stop markers. A
future Sprint 22.4.x mutation runtime will keep the first
line ("IMPLEMENTED") and change the second to "EXECUTED
at version N".

Architecture boundary (Sprint 22.4-E spec Task 3):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import EvolutionAuditRecord
from .store import AuditStore


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_record(record: EvolutionAuditRecord) -> List[str]:
    lines: List[str] = []
    lines.append("### audit `" + record.audit_id + "`")
    lines.append("")
    lines.append("- transaction_id: `" + _safe(record.transaction_id) + "`")
    lines.append("- proposal_id: `" + _safe(record.proposal_id) + "`")
    if record.previous_version is None:
        lines.append("- previous_version: (initial)")
    else:
        lines.append("- previous_version: `"
                     + str(record.previous_version) + "`")
    lines.append("- new_version: `" + str(record.new_version) + "`")
    lines.append("- change_type: `" + _safe(record.change_type) + "`")
    lines.append("- reviewer: `" + _safe(record.reviewer) + "`")
    lines.append("- reason: " + _safe(record.reason))
    lines.append("- rollback_reference: `"
                 + _safe(record.rollback_reference) + "`")
    if record.after_snapshot is None:
        lines.append("- after_snapshot: (not yet computed in V1)")
    else:
        lines.append(
            "- after_snapshot_keys: "
            + ", ".join(
                "`" + str(k) + "`" for k in sorted(record.after_snapshot.keys())
            )
        )
    if record.before_snapshot:
        lines.append(
            "- before_snapshot_keys: "
            + ", ".join(
                "`" + str(k) + "`" for k in sorted(record.before_snapshot.keys())
            )
        )
    return lines


def generate_report(
    store: AuditStore,
    target_identity: str,
    *,
    title: str = "Evolution Audit Log Report",
) -> str:
    """Render a Markdown report of an ``AuditStore`` for one KO.

    The report is pure over the store. It does not mutate the
    store and does not call any engine.
    """
    history = store.history(target_identity)
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    lines.append("## Target Identity")
    lines.append("")
    lines.append("- target_identity: `" + _safe(target_identity) + "`")
    lines.append("- total_audit_records: " + str(len(history)))
    lines.append("")

    lines.append("## Audit History")
    lines.append("")
    if not history:
        lines.append("(no audit records for this identity)")
    else:
        for r in history:
            lines.extend(_render_record(r))
            lines.append("")
    lines.append("")

    lines.append("## Status")
    lines.append("")
    lines.append("- Audit Schema Foundation: **IMPLEMENTED**")
    lines.append("- Knowledge Mutation: **NOT IMPLEMENTED**")
    lines.append("")
    lines.append(
        "  The V1 audit layer records EvolutionAuditRecord"
    )
    lines.append(
        "  entries in an append-only store. The 13-field schema"
    )
    lines.append(
        "  (audit_id, transaction_id, proposal_id, target_identity,"
    )
    lines.append(
        "  previous_version, new_version, before_snapshot,"
    )
    lines.append(
        "  after_snapshot, change_type, reason, reviewer,"
    )
    lines.append(
        "  created_at, rollback_reference) is locked. The"
    )
    lines.append(
        "  rollback_reference field is stored but never used;"
    )
    lines.append(
        "  the store has no restore/rollback/apply method. A"
    )
    lines.append(
        "  future Sprint 22.4.x will consume the audit log under"
    )
    lines.append(
        "  ADR-020 Rules 1-5 and a new rollback ADR."
    )
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
