"""IntakeManager (Sprint 20.7 spec section 4).

The intake layer is the stomach: it accepts incoming information,
tracks its lifecycle, and routes it through governance. It NEVER
writes to the Knowledge Corpus directly and NEVER bypasses
governance.

Allowed entry points:
  create(raw_case)        -> NEW raw case
  list_by_status(status)  -> inspect
  submit_for_review(id)   -> NEW -> REVIEW_REQUIRED
  validate(id)            -> REVIEW_REQUIRED -> VALIDATED
  promote(id)             -> VALIDATED -> PROMOTED -> ACTIVE
  reject(id, reason)      -> records the rejection without advancing

Disallowed:
  - direct corpus write
  - skipping governance validation
  - mutating a stored RawCaseObject in place
  - reading or writing a Knowledge Object outside governance

Architecture: the manager depends on governance, NOT on
retrieval, decision, trust, or recommendation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from caseos.knowledge.intake.converter import (
    to_candidate_knowledge_object,
    summarise_candidate,
)
from caseos.knowledge.intake.object import (
    RawCaseObject,
    new_raw_case,
)
from caseos.knowledge.intake.status import (
    IntakeStatus,
    LIFECYCLE_ORDER,
    is_forward,
)
from caseos.knowledge.governance import (
    validate_for_governance,
    promote as governance_promote,
    PromotionEvent,
    PromotionError,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class TransitionRecord:
    "One append-only lifecycle event.",
    raw_id: str
    from_status: str
    to_status: str
    at: str
    reason: str = ""
    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "from": self.from_status,
            "to": self.to_status,
            "at": self.at,
            "reason": self.reason,
        }


class IntakeError(RuntimeError):
    pass


class IntakeManager:
    "In-memory intake manager (Sprint 20.7).",
    def __init__(self) -> None:
        self._cases: dict[str, RawCaseObject] = {}
        self._transitions: list[TransitionRecord] = []
        self._promotion_events: list[PromotionEvent] = []
    def get(self, raw_id: str) -> Optional[RawCaseObject]:
        rc = self._cases.get(raw_id)
        return rc.copy() if rc is not None else None
    def list_by_status(self, status: IntakeStatus) -> list[RawCaseObject]:
        return [rc.copy() for rc in self._cases.values() if rc.status == status]
    def all_cases(self) -> list[RawCaseObject]:
        return [rc.copy() for rc in self._cases.values()]
    def transitions(self, raw_id: str) -> list[TransitionRecord]:
        return [t for t in self._transitions if t.raw_id == raw_id]
    def promotion_events(self) -> list[PromotionEvent]:
        return list(self._promotion_events)
    def create(self, raw_case: RawCaseObject) -> RawCaseObject:
        if not isinstance(raw_case, RawCaseObject):
            raise IntakeError("create() expects a RawCaseObject")
        if raw_case.status != IntakeStatus.NEW:
            raise IntakeError("new raw cases must start in NEW")
        if raw_case.id in self._cases:
            raise IntakeError("duplicate raw id: " + raw_case.id)
        stored = raw_case.copy()
        self._cases[stored.id] = stored
        return stored.copy()
    def create_from_kwargs(self, **kwargs) -> RawCaseObject:
        return self.create(new_raw_case(**kwargs))
    def _record_transition(self, raw_id: str, frm: IntakeStatus, to: IntakeStatus, reason: str = "") -> None:
        if not is_forward(frm, to):
            raise IntakeError("transition " + frm.value + " -> " + to.value + " is not forward")
        self._transitions.append(
            TransitionRecord(raw_id=raw_id, from_status=frm.value, to_status=to.value, at=_now_iso(), reason=reason),
        )
        stored = self._cases[raw_id]
        updated = stored.copy()
        updated.status = to
        self._cases[raw_id] = updated
    def submit_for_review(self, raw_id: str) -> RawCaseObject:
        rc = self._cases.get(raw_id)
        if rc is None:
            raise IntakeError("unknown raw id: " + raw_id)
        if rc.status != IntakeStatus.NEW:
            raise IntakeError("submit_for_review requires NEW, got " + rc.status.value)
        self._record_transition(raw_id, IntakeStatus.NEW, IntakeStatus.REVIEW_REQUIRED, "queued for governance review")
        return self.get(raw_id)
    def validate(self, raw_id: str) -> dict[str, Any]:
        rc = self._cases.get(raw_id)
        if rc is None:
            raise IntakeError("unknown raw id: " + raw_id)
        if rc.status not in (IntakeStatus.REVIEW_REQUIRED, IntakeStatus.VALIDATED):
            raise IntakeError("validate requires REVIEW_REQUIRED, got " + rc.status.value)
        candidate = to_candidate_knowledge_object(rc.copy())
        result = validate_for_governance(candidate)
        if result.valid:
            self._record_transition(raw_id, IntakeStatus.REVIEW_REQUIRED, IntakeStatus.VALIDATED, "governance passed")
        else:
            all_errors = list(result.base_errors) + list(result.governance_errors)
            sep = "; "
            msg = (sep.join(all_errors)) if all_errors else "no specific error reported"
            self._transitions.append(
                TransitionRecord(
                    raw_id=raw_id,
                    from_status=rc.status.value,
                    to_status=rc.status.value,
                    at=_now_iso(),
                    reason="governance failed: " + msg,
                )
            )
        return {
            "raw_id": raw_id,
            "candidate": summarise_candidate(candidate),
            "valid": result.valid,
            "missing": list(result.base_missing),
            "errors": list(result.base_errors) + list(result.governance_errors),
        }
    def promote(self, raw_id: str) -> PromotionEvent:
        rc = self._cases.get(raw_id)
        if rc is None:
            raise IntakeError("unknown raw id: " + raw_id)
        if rc.status != IntakeStatus.VALIDATED:
            raise IntakeError("promote requires VALIDATED, got " + rc.status.value)
        candidate = to_candidate_knowledge_object(rc.copy())
        try:
            event = governance_promote(candidate, "DecisionPattern", note="promoted via intake " + raw_id)
        except PromotionError as e:
            self._transitions.append(
                TransitionRecord(
                    raw_id=raw_id,
                    from_status=rc.status.value,
                    to_status=rc.status.value,
                    at=_now_iso(),
                    reason="governance refused promotion: " + str(e),
                )
            )
            raise
        self._promotion_events.append(event)
        self._record_transition(raw_id, IntakeStatus.VALIDATED, IntakeStatus.PROMOTED, "governance produced KO " + event.target_identity)
        self._record_transition(raw_id, IntakeStatus.PROMOTED, IntakeStatus.ACTIVE, "KO is active in corpus")
        return event
    def reject(self, raw_id: str, reason: str) -> None:
        rc = self._cases.get(raw_id)
        if rc is None:
            raise IntakeError("unknown raw id: " + raw_id)
        self._transitions.append(
            TransitionRecord(
                raw_id=raw_id,
                from_status=rc.status.value,
                to_status=rc.status.value,
                at=_now_iso(),
                reason="rejected: " + reason,
            )
        )
    def status_counts(self) -> dict[str, int]:
        out: dict[str, int] = {s.value: 0 for s in IntakeStatus}
        for rc in self._cases.values():
            out[rc.status.value] += 1
        return out
    def rejected_count(self) -> int:
        return sum(1 for t in self._transitions if t.reason.startswith("rejected:"))


__all__ = [
    "IntakeError",
    "TransitionRecord",
    "IntakeManager",
]
