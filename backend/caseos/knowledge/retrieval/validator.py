"""Knowledge Retrieval Validator V1 (Sprint 24.0-A).

The validator is the **runtime guard** that enforces the
retrieval contract on a ``RetrievalQuery`` instance. It
is stateless: every call is a pure function of the input.

Single-record checks (Q1..Q8):

    Q1  query_id is a non-empty string
    Q2  version >= 1
    Q3  1 <= limit <= 1000
    Q4  match_mode is in MATCH_MODE_ALLOW_LIST
    Q5  sort_by is in SORT_BY_ALLOW_LIST
    Q6  sort_order is in SORT_ORDER_ALLOW_LIST
    Q7  at least one of query_text / query_fields / filters is
        provided (the query must actually ask for something)
    Q8  every key in ``filters`` is a valid KO V1 field (i.e.
        a member of ``caseos.knowledge.object.schema.REQUIRED_FIELDS``)

The validator returns a ``RetrievalValidationResult`` with a
boolean verdict and a tuple of human-readable error messages.

Architecture boundary (Sprint 24.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object  (KO schema)
        * caseos.knowledge.retrieval (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional, Tuple

from caseos.knowledge.object.schema import REQUIRED_FIELDS as KO_REQUIRED_FIELDS

from .object import RetrievalQuery
from .schema import (
    MATCH_MODE_ALLOW_LIST,
    MAX_LIMIT,
    MIN_LIMIT,
    SORT_BY_ALLOW_LIST,
    SORT_ORDER_ALLOW_LIST,
)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RetrievalValidationResult:
    """Outcome of a ``RetrievalValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: tuple of human-readable error messages.
            Empty when ``valid`` is True.
        rule_failures: tuple of rule identifiers (Q1..Q8) that
            failed. Useful for diagnostic output.
    """

    valid: bool
    errors: Tuple[str, ...] = ()
    rule_failures: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class RetrievalValidator:
    """Stateless validator. ``validate`` is a pure function."""

    def validate(
        self,
        query: Optional[RetrievalQuery],
    ) -> RetrievalValidationResult:
        """Validate a ``RetrievalQuery`` against the V1 contract.

        First failure of each rule contributes one error.
        Multiple rules can fail at once; the validator does
        not short-circuit (so callers see the full picture).
        """
        errors: list[str] = []
        failed: list[str] = []

        if query is None:
            return RetrievalValidationResult(
                valid=False,
                errors=("query is None",),
                rule_failures=("Q0",),
            )

        # ---- Q1: query_id ---------------------------------------
        qid = getattr(query, "query_id", None)
        if not _is_nonempty_str(qid):
            errors.append("Q1: query_id must be a non-empty string")
            failed.append("Q1")

        # ---- Q2: version ----------------------------------------
        version = getattr(query, "version", None)
        if not isinstance(version, int) or version < 1:
            errors.append(
                "Q2: version must be a positive integer (>= 1); got "
                + repr(version)
            )
            failed.append("Q2")

        # ---- Q3: 1 <= limit <= MAX_LIMIT -----------------------
        limit = getattr(query, "limit", None)
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit < MIN_LIMIT
            or limit > MAX_LIMIT
        ):
            errors.append(
                "Q3: limit must be an integer between "
                + str(MIN_LIMIT)
                + " and "
                + str(MAX_LIMIT)
                + "; got "
                + repr(limit)
            )
            failed.append("Q3")

        # ---- Q4: match_mode in allow-list -----------------------
        mm = getattr(query, "match_mode", None)
        if not _is_nonempty_str(mm) or mm not in MATCH_MODE_ALLOW_LIST:
            errors.append(
                "Q4: match_mode must be one of "
                + ", ".join(sorted(MATCH_MODE_ALLOW_LIST))
                + "; got "
                + repr(mm)
            )
            failed.append("Q4")

        # ---- Q5: sort_by in allow-list -------------------------
        sb = getattr(query, "sort_by", None)
        if not _is_nonempty_str(sb) or sb not in SORT_BY_ALLOW_LIST:
            errors.append(
                "Q5: sort_by must be one of "
                + ", ".join(sorted(SORT_BY_ALLOW_LIST))
                + "; got "
                + repr(sb)
            )
            failed.append("Q5")

        # ---- Q6: sort_order in allow-list ----------------------
        so = getattr(query, "sort_order", None)
        if not _is_nonempty_str(so) or so not in SORT_ORDER_ALLOW_LIST:
            errors.append(
                "Q6: sort_order must be one of "
                + ", ".join(sorted(SORT_ORDER_ALLOW_LIST))
                + "; got "
                + repr(so)
            )
            failed.append("Q6")

        # ---- Q7: at least one of {query_text, query_fields,
        #                            filters} must be provided --
        qt = getattr(query, "query_text", "")
        qfields = getattr(query, "query_fields", [])
        filters = getattr(query, "filters", {})
        qt_present = isinstance(qt, str) and bool(qt.strip())
        qfields_present = isinstance(qfields, (list, tuple)) and len(qfields) > 0
        filters_present = isinstance(filters, dict) and len(filters) > 0
        if not (qt_present or qfields_present or filters_present):
            errors.append(
                "Q7: at least one of query_text, query_fields, "
                "filters must be provided"
            )
            failed.append("Q7")

        # ---- Q8: filters keys must be valid KO V1 fields -------
        if isinstance(filters, dict) and len(filters) > 0:
            bad_keys = sorted(
                k for k in filters.keys() if k not in KO_REQUIRED_FIELDS
            )
            if bad_keys:
                errors.append(
                    "Q8: filters contains keys that are not valid "
                    "KO V1 fields: "
                    + ", ".join(bad_keys)
                )
                failed.append("Q8")

        return RetrievalValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            rule_failures=tuple(failed),
        )


__all__ = ["RetrievalValidator", "RetrievalValidationResult"]
