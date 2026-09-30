"""Terminal validator (Sprint 26.0-A, Terminal MVP V1).

Pure, deterministic runtime guard. Consumes a ``TerminalRequest``
and a ``TerminalContract`` and returns a
``TerminalValidationResult``.

Algorithm V1 (fail-fast, first-failure-wins):

    T1  request must be a TerminalRequest
    T2  request_id must be a non-empty string
    T3  site_type must be a non-empty string
    T4  site_description OR uploaded_asset_ids must be non-empty
    T5  site_area, if set, must be > 0
    T6  age_range, if non-empty, must be a non-empty plain string
    T7  limit (provided by service / caller) must be >= 1
    T8  tuple fields must not contain empty strings

The validator NEVER mutates the input request.
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from .contract import (
    DEFAULT_TERMINAL_CONTRACT,
    MIN_LIMIT,
    TerminalContract,
)
from .object import (
    TerminalRequest,
    TerminalValidationResult,
)


class TerminalValidatorError(ValueError):
    """Base error for the Terminal validator."""


class TerminalValidator:
    """V1 deterministic Terminal gate."""

    ENGINE_NAME: str = "TerminalValidator V1"

    def __init__(
        self,
        contract: Optional[TerminalContract] = None,
    ) -> None:
        if contract is None:
            contract = DEFAULT_TERMINAL_CONTRACT
        if not isinstance(contract, TerminalContract):
            raise TerminalValidatorError(
                "contract must be a TerminalContract or None; got "
                + type(contract).__name__
            )
        self.contract: TerminalContract = contract

    # ---- public ----------------------------------------------------

    def validate(
        self,
        request,
        *,
        limit: Optional[int] = None,
    ) -> TerminalValidationResult:
        """Run the gate.

        ``limit`` is the desired Top-K; when None we use the
        contract default. The validator never mutates ``request``.
        """
        # T1 -- request type
        if not isinstance(request, TerminalRequest):
            return TerminalValidationResult(
                valid=False,
                rule_id="T1_request_type",
                reason=(
                    "request must be a TerminalRequest; got "
                    + type(request).__name__
                ),
            )

        # T2 -- request_id present
        if (
            not isinstance(request.request_id, str)
            or not request.request_id.strip()
        ):
            return TerminalValidationResult(
                valid=False,
                rule_id="T2_request_id_present",
                reason="request_id is empty",
                request_id=request.request_id,
            )

        # T3 -- site_type present
        if (
            not isinstance(request.site_type, str)
            or not request.site_type.strip()
        ):
            return TerminalValidationResult(
                valid=False,
                rule_id="T3_site_type_present",
                reason="site_type is empty",
                request_id=request.request_id,
            )

        # T4 -- site_description OR uploaded_asset_ids
        has_description = bool(
            isinstance(request.site_description, str)
            and request.site_description.strip()
        )
        has_assets = bool(
            isinstance(request.uploaded_asset_ids, tuple)
            and len(request.uploaded_asset_ids) > 0
        )
        if not (has_description or has_assets):
            return TerminalValidationResult(
                valid=False,
                rule_id="T4_description_or_assets",
                reason=(
                    "site_description and uploaded_asset_ids are "
                    "both empty; at least one is required"
                ),
                request_id=request.request_id,
            )

        # T5 -- site_area, if set, must be > 0
        if request.site_area is not None:
            if not isinstance(request.site_area, (int, float)):
                return TerminalValidationResult(
                    valid=False,
                    rule_id="T5_site_area_positive_when_set",
                    reason=(
                        "site_area must be a number when provided; got "
                        + type(request.site_area).__name__
                    ),
                    request_id=request.request_id,
                )
            if request.site_area <= 0:
                return TerminalValidationResult(
                    valid=False,
                    rule_id="T5_site_area_positive_when_set",
                    reason=(
                        "site_area must be > 0 when set; got "
                        + repr(request.site_area)
                    ),
                    request_id=request.request_id,
                )

        # T6 -- age_range, if non-empty, must be a plain string
        if request.age_range is not None and request.age_range != "":
            if (
                not isinstance(request.age_range, str)
                or not request.age_range.strip()
            ):
                return TerminalValidationResult(
                    valid=False,
                    rule_id="T6_age_range_well_formed",
                    reason=(
                        "age_range must be a non-empty string when set; "
                        "got " + repr(request.age_range)
                    ),
                    request_id=request.request_id,
                )

        # T7 -- limit >= 1 (when supplied)
        if limit is not None:
            if not isinstance(limit, int):
                try:
                    limit = int(limit)
                except (TypeError, ValueError):
                    return TerminalValidationResult(
                        valid=False,
                        rule_id="T7_limit_in_range",
                        reason=(
                            "limit must be an int; got "
                            + type(limit).__name__
                        ),
                        request_id=request.request_id,
                    )
            if limit < MIN_LIMIT:
                return TerminalValidationResult(
                    valid=False,
                    rule_id="T7_limit_in_range",
                    reason=(
                        "limit must be >= "
                        + str(MIN_LIMIT)
                        + "; got "
                        + repr(limit)
                    ),
                    request_id=request.request_id,
                )

        # T8 -- tuple fields must not contain empty strings
        for fname in ("preferred_functions", "uploaded_asset_ids"):
            value = getattr(request, fname)
            if not isinstance(value, tuple):
                return TerminalValidationResult(
                    valid=False,
                    rule_id="T8_tuple_no_empty_strings",
                    reason=(
                        fname + " must be a tuple; got "
                        + type(value).__name__
                    ),
                    request_id=request.request_id,
                )
            for item in value:
                if not isinstance(item, str) or not item:
                    return TerminalValidationResult(
                        valid=False,
                        rule_id="T8_tuple_no_empty_strings",
                        reason=(
                            fname + " contains an empty or non-string entry"
                        ),
                        request_id=request.request_id,
                    )

        # ---- all checks passed -------------------------------------
        return TerminalValidationResult(
            valid=True,
            rule_id="OK",
            reason="all V1 Terminal rules satisfied",
            request_id=request.request_id,
        )


__all__ = [
    "TerminalValidatorError",
    "TerminalValidator",
]
