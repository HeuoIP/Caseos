"""Intake -> Case Knowledge Adapter V1 (Sprint 25.1-A inferred).

This adapter is the bridge between the **pre-knowledge**
intake layer (``caseos.knowledge.intake.RawCaseObject``)
and the **contract** ingestion layer (``CaseKnowledge``
defined in 25.0-A).

Responsibilities (V1)
---------------------

    * Convert a ``RawCaseObject`` into a ``CaseKnowledge``.
    * Validate the source kind / ID shape *before* mapping.
    * Preserve immutability: the adapter NEVER mutates the
      raw case or its collections.
    * Surface clear errors (``IntakeAdapterError``) for
      unsupported shapes; never silently swallow them.

Mapping V1
----------

    RawCaseObject           -> CaseKnowledge
    ----------------------------------------------
    id                      -> case_id   (CK-prefix stripped
                                            and re-applied if
                                            needed)
    source                  -> source
    (constant)              -> source_kind = "intake"
    title                   -> title
    description             -> description
    files                   -> linked_assets
    candidate_tags          -> tags
    source_reference        -> origin_reference
    created_at              -> created_at (preserved)
    (constant)              -> created_by = "intake"
    (constant)              -> requires_human_review = True
    (none)                  -> knowledge_id / knowledge_version
                                (left empty; future sprints
                                 will fill these once the
                                 KO is promoted into corpus)

Architecture boundary
---------------------

    This module is the ONLY place inside ``caseos.knowledge.ingestion``
    that may import from ``caseos.knowledge.intake``. The rest of
    the ingestion package stays pure-schema.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from caseos.knowledge.intake.object import RawCaseObject

from ..object import (
    SOURCE_KIND_INTAKE,
    CaseKnowledge,
    CaseKnowledgeError,
    new_case_knowledge,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class IntakeAdapterError(ValueError):
    """Raised when a RawCaseObject cannot be adapted."""


# ---------------------------------------------------------------------------
# Duck-typed raw record protocol
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawIntakeRecord:
    """Duck-typed view of a raw intake record.

    The adapter only consumes these fields; this dataclass
    exists so that callers can pre-validate the shape of a
    non-``RawCaseObject`` input without coupling the adapter
    to the intake module's exact class.

    Tests use this to feed arbitrary inputs through the
    adapter without going through ``RawCaseObject``'s
    full lifecycle machinery.
    """

    id: str
    source: str
    title: str = ""
    description: str = ""
    files: Tuple[str, ...] = ()
    candidate_tags: Tuple[str, ...] = ()
    source_reference: str = ""
    created_at: str = ""
    notes: str = ""

    @classmethod
    def from_raw_case(cls, raw: Any) -> "RawIntakeRecord":
        """Construct a RawIntakeRecord from a RawCaseObject
        (or a duck-typed equivalent)."""
        if not isinstance(raw, RawCaseObject) and not _looks_like_raw(raw):
            raise IntakeAdapterError(
                "input is not a RawCaseObject and lacks the "
                "duck-typed shape; got " + type(raw).__name__
            )
        files = tuple(getattr(raw, "files", ()) or ())
        tags = tuple(getattr(raw, "candidate_tags", ()) or ())
        return cls(
            id=str(getattr(raw, "id", "") or ""),
            source=str(getattr(raw, "source", "") or ""),
            title=str(getattr(raw, "title", "") or ""),
            description=str(getattr(raw, "description", "") or ""),
            files=tuple(str(f) for f in files),
            candidate_tags=tuple(str(t) for t in tags),
            source_reference=str(
                getattr(raw, "source_reference", "") or ""
            ),
            created_at=str(getattr(raw, "created_at", "") or ""),
            notes=str(getattr(raw, "notes", "") or ""),
        )


def _looks_like_raw(obj: Any) -> bool:
    return (
        hasattr(obj, "id")
        and hasattr(obj, "source")
        and hasattr(obj, "title")
    )


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntakeAdapter:
    """V1 adapter: RawCaseObject -> CaseKnowledge.

    The dataclass is frozen; callers may share one instance
    across many adaptations. All instance state is pure
    configuration.
    """

    source_kind: str = SOURCE_KIND_INTAKE
    created_by: str = "intake"
    case_id_prefix: str = "CK-"
    preserve_created_at: bool = True
    require_human_review: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, str) or not self.source_kind:
            raise IntakeAdapterError(
                "source_kind must be a non-empty string"
            )
        if not isinstance(self.case_id_prefix, str):
            raise IntakeAdapterError(
                "case_id_prefix must be a string; got "
                + type(self.case_id_prefix).__name__
            )

    # ---- public ----------------------------------------------------

    def adapt(self, raw: Any) -> CaseKnowledge:
        """Convert one raw record into a CaseKnowledge.

        The raw record may be either a ``RawCaseObject`` or
        any duck-typed object exposing the fields listed on
        ``RawIntakeRecord``. The function never mutates ``raw``.
        """
        view = RawIntakeRecord.from_raw_case(raw)
        return self._build(view)

    def adapt_many(
        self, raws: Iterable[Any]
    ) -> List[CaseKnowledge]:
        """Convert an iterable of raw records.

        Each input is adapted independently. The first failure
        aborts the batch and surfaces as ``IntakeAdapterError``;
        partial output is not returned. The function never
        mutates any input.
        """
        out: list = []
        for r in raws:
            out.append(self.adapt(r))
        return out

    # ---- private helpers ------------------------------------------

    def _build(self, view: RawIntakeRecord) -> CaseKnowledge:
        # ID guard.
        if not view.id or not view.id.strip():
            raise IntakeAdapterError(
                "RawCaseObject.id is empty; cannot adapt"
            )
        if not view.source or not view.source.strip():
            raise IntakeAdapterError(
                "RawCaseObject.source is empty; cannot adapt"
            )

        # Normalise case_id: strip a stale CK- prefix and
        # re-apply our prefix. This keeps raw-side ids round-trippable.
        raw_id = view.id.strip()
        prefix = self.case_id_prefix
        if prefix and raw_id.startswith(prefix):
            stripped = raw_id[len(prefix):]
        else:
            stripped = raw_id
        new_case_id = prefix + stripped

        # Build kwargs. When ``preserve_created_at`` is False we
        # omit ``created_at`` entirely so the dataclass default
        # factory generates a fresh ISO timestamp; passing
        # ``created_at=""`` would leave the field empty.
        common: dict = dict(
            case_id=new_case_id,
            source=view.source,
            source_kind=self.source_kind,
            title=view.title,
            description=view.description,
            knowledge_id="",
            knowledge_version=1,
            tags=tuple(view.candidate_tags),
            linked_assets=tuple(view.files),
            origin_reference=view.source_reference,
            created_by=self.created_by,
            requires_human_review=self.require_human_review,
        )
        if self.preserve_created_at:
            common["created_at"] = view.created_at

        try:
            return CaseKnowledge(**common)
        except CaseKnowledgeError as exc:
            raise IntakeAdapterError(
                "CaseKnowledge build failed for raw id="
                + repr(view.id) + ": " + str(exc)
            ) from exc


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


DEFAULT_INTAKE_ADAPTER: IntakeAdapter = IntakeAdapter()


def adapt_raw_case(
    raw: Any,
    *,
    adapter: Optional[IntakeAdapter] = None,
) -> CaseKnowledge:
    """Adapt one raw record using the default adapter (or override)."""
    return (adapter or DEFAULT_INTAKE_ADAPTER).adapt(raw)


def adapt_raw_cases(
    raws: Iterable[Any],
    *,
    adapter: Optional[IntakeAdapter] = None,
) -> List[CaseKnowledge]:
    """Adapt a batch of raw records using the default adapter."""
    return (adapter or DEFAULT_INTAKE_ADAPTER).adapt_many(raws)
