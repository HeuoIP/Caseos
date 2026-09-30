"""Terminal contract constants (Sprint 26.0-A, Terminal MVP V1).

Pure constants and the ``TerminalContract`` rule table. The
validator (``validator.py``) consumes this contract to decide
whether a ``TerminalRequest`` is acceptable.

Rules V1 (Sprint 26.0-A spec section 9):

    T1  request must be a TerminalRequest
    T2  request_id must be a non-empty string
    T3  site_type must be a non-empty string
    T4  site_description AND uploaded_asset_ids must NOT both be empty
    T5  site_area, if set, must be > 0
    T6  age_range, if non-empty, must be a plain non-empty string
    T7  limit >= 1
    T8  tuple fields must not contain empty strings

The numeric bounds below are intentionally generous; they exist
to keep the contract enumerable. ``TerminalService`` clamps
``limit`` to ``LIMIT_BOUNDS`` before constructing the
``RetrievalQuery``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


# ---------------------------------------------------------------------------
# Numeric bounds
# ---------------------------------------------------------------------------


DEFAULT_LIMIT: int = 5
MIN_LIMIT: int = 1
MAX_LIMIT: int = 50


# ---------------------------------------------------------------------------
# Rule labels
# ---------------------------------------------------------------------------


RULE_LABELS: Tuple[str, ...] = (
    "T1_request_type",
    "T2_request_id_present",
    "T3_site_type_present",
    "T4_description_or_assets",
    "T5_site_area_positive_when_set",
    "T6_age_range_well_formed",
    "T7_limit_in_range",
    "T8_tuple_no_empty_strings",
)


# ---------------------------------------------------------------------------
# TerminalContract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TerminalContract:
    """The V1 Terminal rule table.

    Frozen dataclass; callers may freely share it. The validator
    consumes this contract to decide whether a ``TerminalRequest``
    is acceptable.
    """

    default_limit: int = DEFAULT_LIMIT
    min_limit: int = MIN_LIMIT
    max_limit: int = MAX_LIMIT
    allow_partial_information: bool = True

    def __post_init__(self) -> None:
        if self.default_limit < self.min_limit:
            raise ValueError(
                "default_limit must be >= min_limit; got "
                + repr(self.default_limit) + " < "
                + repr(self.min_limit)
            )
        if self.max_limit < self.min_limit:
            raise ValueError(
                "max_limit must be >= min_limit; got "
                + repr(self.max_limit) + " < "
                + repr(self.min_limit)
            )
        if self.default_limit > self.max_limit:
            raise ValueError(
                "default_limit must be <= max_limit; got "
                + repr(self.default_limit) + " > "
                + repr(self.max_limit)
            )

    # ---- Convenience predicates ----------------------------------
    def limit_in_range(self, n: int) -> bool:
        return self.min_limit <= n <= self.max_limit

    def clamp_limit(self, n: int) -> int:
        if not isinstance(n, int):
            try:
                n = int(n)
            except (TypeError, ValueError):
                return self.default_limit
        if n < self.min_limit:
            return self.min_limit
        if n > self.max_limit:
            return self.max_limit
        return n

    def summary(self) -> Tuple[str, ...]:
        """Return a stable tuple of rule names for reporting."""
        return RULE_LABELS

    def describe(self) -> dict:
        return {
            "default_limit": self.default_limit,
            "min_limit": self.min_limit,
            "max_limit": self.max_limit,
            "allow_partial_information": self.allow_partial_information,
            "rules": list(self.summary()),
        }


# ---------------------------------------------------------------------------
# Default singleton
# ---------------------------------------------------------------------------


DEFAULT_TERMINAL_CONTRACT: TerminalContract = TerminalContract()


def default_contract() -> TerminalContract:
    return DEFAULT_TERMINAL_CONTRACT


__all__ = [
    "DEFAULT_LIMIT",
    "MIN_LIMIT",
    "MAX_LIMIT",
    "RULE_LABELS",
    "TerminalContract",
    "DEFAULT_TERMINAL_CONTRACT",
    "default_contract",
]
