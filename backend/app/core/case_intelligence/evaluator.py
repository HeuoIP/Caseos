"""Stage 4: Case Evaluation (ADR-012).

The V1 evaluator is **manual** -- it accepts the five weighted
scores and the transferability object from a human reviewer (or an
external tool). It does NOT call any LLM and does NOT auto-score.

What it does:

  1. Validates every score is in its ADR-012 weight range.
  2. Computes ``total_score`` as the sum of the five components.
  3. Validates the supplied ``total_score`` matches the computed
     sum within ``TOLERANCE`` (default 0.01).
  4. Returns the resulting ``CaseEvaluation``.

V1.2 of the CKO schema also expects ``transferability`` to carry a
non-empty ``applicable_project_types`` list and a non-empty
``limitations`` list; that validation lives in
``Transferability.__post_init__``.
"""

from __future__ import annotations

from typing import Any

from .models import (
    GOLDEN_THRESHOLDS,
    WEIGHTS,
    CaseEvaluation,
    Transferability,
)


# Tolerance for total_score == sum of components equality check.
TOLERANCE: float = 0.01


class EvaluationValidationError(ValueError):
    """Raised when a Case Evaluation payload fails ADR-012 validation."""


class CaseEvaluator:
    """Stage 4 of the Golden Case pipeline.

    Usage::

        ev = CaseEvaluator().evaluate(
            {
                "space_logic_score": 22,
                "experience_logic_score": 23,
                "theme_meaning_logic_score": 16,
                "user_value_score": 13,
                "commercial_logic_score": 7,
                "total_score": 81,
                "transferability": {...},
            }
        )
    """

    def evaluate(self, payload: dict[str, Any]) -> CaseEvaluation:
        """Validate and build a CaseEvaluation from the supplied scores.

        Args:
            payload: A dict with five weighted scores, a ``total_score``
                and a ``transferability`` object. The schema is the same
                as ADR-012 Section 9.

        Returns:
            A ``CaseEvaluation`` with the validated scores and the
            operational tier derived from ``total_score``.

        Raises:
            EvaluationValidationError: on any invalid field.
        """
        scores: dict[str, float] = {}
        for key, max_value in WEIGHTS.items():
            if key not in payload:
                raise EvaluationValidationError(
                    f"Missing required score field: {key!r}"
                )
            try:
                v = float(payload[key])
            except (TypeError, ValueError) as exc:
                raise EvaluationValidationError(
                    f"Score {key!r} is not numeric: {payload[key]!r}"
                ) from exc
            if not 0 <= v <= max_value:
                raise EvaluationValidationError(
                    f"Score {key!r}={v} out of range 0..{max_value}"
                )
            scores[key] = v

        # Total must equal sum of components.
        computed = sum(scores.values())
        if "total_score" not in payload:
            raise EvaluationValidationError(
                "Missing required field: total_score"
            )
        try:
            supplied_total = float(payload["total_score"])
        except (TypeError, ValueError) as exc:
            raise EvaluationValidationError(
                f"total_score is not numeric: {payload['total_score']!r}"
            ) from exc
        if not 0 <= supplied_total <= sum(WEIGHTS.values()):
            raise EvaluationValidationError(
                f"total_score={supplied_total} out of range 0..{sum(WEIGHTS.values())}"
            )
        if abs(supplied_total - computed) > TOLERANCE:
            raise EvaluationValidationError(
                f"total_score={supplied_total} does not match "
                f"sum of components={computed:.2f} (tolerance {TOLERANCE})"
            )

        # Transferability object -- its __post_init__ validates the
        # three required fields and their formats.
        if "transferability" not in payload:
            raise EvaluationValidationError(
                "Missing required field: transferability"
            )
        t_data = payload["transferability"]
        try:
            transfer = Transferability(
                level=str(t_data["level"]),
                applicable_project_types=list(t_data["applicable_project_types"]),
                limitations=list(t_data["limitations"]),
            )
        except KeyError as exc:
            raise EvaluationValidationError(
                f"transferability missing key: {exc.args[0]!r}"
            ) from exc
        except (TypeError, ValueError) as exc:
            raise EvaluationValidationError(
                f"transferability invalid: {exc}"
            ) from exc

        return CaseEvaluation(
            space_logic_score=scores["space_logic_score"],
            experience_logic_score=scores["experience_logic_score"],
            theme_meaning_logic_score=scores["theme_meaning_logic_score"],
            user_value_score=scores["user_value_score"],
            commercial_logic_score=scores["commercial_logic_score"],
            total_score=supplied_total,
            transferability=transfer,
        )

    # ------------------------------------------------------------------
    # Convenience: build a payload from a numbered tuple of scores.
    # ------------------------------------------------------------------

    @staticmethod
    def payload_from_scores(
        space: float,
        experience: float,
        theme: float,
        user: float,
        commercial: float,
        level: str,
        applicable_project_types: list[str],
        limitations: list[str],
    ) -> dict[str, Any]:
        """Return a payload dict whose total_score is computed by this helper.

        This is for tests / scripts that want the evaluator to handle
        the addition. Validation in ``self.evaluate`` will still check
        the supplied ``total_score`` matches.
        """
        total = space + experience + theme + user + commercial
        return {
            "space_logic_score": space,
            "experience_logic_score": experience,
            "theme_meaning_logic_score": theme,
            "user_value_score": user,
            "commercial_logic_score": commercial,
            "total_score": total,
            "transferability": {
                "level": level,
                "applicable_project_types": applicable_project_types,
                "limitations": limitations,
            },
        }


__all__ = ["CaseEvaluator", "EvaluationValidationError", "TOLERANCE"]
