"""Knowledge Object validator (Sprint 20.5).

Validates a Knowledge Object against the ADR-015 9-field contract:

    1. identity            (string, non-empty)        -- required
    2. situation_context   (dict or string, non-empty) -- required
    3. observation         (list or string, non-empty) -- required
    4. diagnosis           (string, non-empty)         -- required
    5. decision            (string or dict, non-empty) -- required
    6. principle           (string, non-empty)         -- required
    7. applicability       (dict, non-empty list)      -- MANDATORY
    8. boundary            (list or string, non-empty) -- MANDATORY
    9. feedback            (list)                      -- soft (empty OK)

Boundary and Applicability are MANDATORY per Sprint 20.5 spec
section 2. A KO that is missing either must fail validation.

The distinction between "missing" and "invalid" is preserved:
  * A field that is *absent* from the dict OR is `None` is added
    to `missing`.
  * For mandatory fields (boundary, applicability), an *absent*
    field is also reported as a "mandatory field missing" error.
  * A field that is *present* but invalid (e.g. boundary=[]) is
    reported in `errors`, not `missing` -- this lets the report
    distinguish "the file has the field but its content is wrong"
    from "the file forgot the field entirely".
  * `feedback` is treated as a *soft* field: an empty list is
    accepted (means "no recorded feedback yet").

The validator is deterministic and Python-stdlib-only: no
network, no LLM, no embedding. It runs in O(1) per field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ADR-015 9-field contract. The order here is the canonical
# reporting order used by the migration report.
REQUIRED_FIELDS: tuple[str, ...] = (
    "identity",
    "situation_context",
    "observation",
    "diagnosis",
    "decision",
    "principle",
    "applicability",
    "boundary",
    "feedback",
)

# Boundary and Applicability are the two mandatory fields per
# Sprint 20.5 spec section 2. A KO missing either of them is
# rejected regardless of how good the other fields look.
MANDATORY_FIELDS: frozenset[str] = frozenset({"applicability", "boundary"})

# Soft fields: present (even empty) is acceptable. The field is
# not added to `missing` even if it is empty.
SOFT_FIELDS: frozenset[str] = frozenset({"feedback"})


@dataclass
class ValidationResult:
    """One validator run, per Knowledge Object.

    Attributes:
        identity: KO identity (or "<unknown>" if missing)
        valid:    True iff all required fields are present and non-empty
        missing:  list of required field names that are absent
        errors:   list of human-readable error messages
    """

    identity: str
    valid: bool
    missing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "valid": self.valid,
            "missing": list(self.missing),
            "errors": list(self.errors),
        }


# ---------------------------------------------------------------------------
# Field-level predicates
# ---------------------------------------------------------------------------

def _is_absent(ko: dict, field_name: str) -> bool:
    """A field is "absent" if it is not in the dict or is None."""
    if field_name not in ko:
        return True
    return ko[field_name] is None


def _is_empty(value: Any) -> bool:
    """A field is "empty" if it carries no usable content.

    Empty means:
      * empty string ""
      * empty list []
      * empty dict {}
    Boolean False and 0 are not empty (they carry meaning).
    """
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _applicability_ok(value: Any) -> tuple[bool, str | None]:
    """Applicability must be a dict with a non-empty list under
    either `suitable` or `suitable_when`. Returns (ok, error_msg).
    """
    if not isinstance(value, dict):
        return False, "applicability must be a dict"
    suitable = value.get("suitable") or value.get("suitable_when")
    if not isinstance(suitable, list) or not suitable:
        return False, (
            "applicability must declare a non-empty list under "
            "`suitable` or `suitable_when`"
        )
    return True, None


def _boundary_ok(value: Any) -> tuple[bool, str | None]:
    """Boundary must be a non-empty list (preferred) or a non-empty
    string. Returns (ok, error_msg).
    """
    if isinstance(value, list):
        if not value:
            return False, "boundary must be a non-empty list"
        return True, None
    if isinstance(value, str) and value.strip():
        return True, None
    return False, "boundary must be a non-empty list or non-empty string"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def validate_knowledge_object(ko: Any) -> ValidationResult:
    """Validate a single Knowledge Object against the ADR-015 contract.

    Returns a ValidationResult. Never raises.
    """

    if not isinstance(ko, dict):
        return ValidationResult(
            identity="<unknown>",
            valid=False,
            missing=list(REQUIRED_FIELDS),
            errors=[f"top-level value must be a dict, got {type(ko).__name__}"],
        )

    identity = ko.get("identity")
    identity_str = str(identity) if identity is not None else "<unknown>"

    missing: list[str] = []
    errors: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if _is_absent(ko, field_name):
            # Absent fields go into `missing`. Mandatory fields
            # additionally get a `mandatory field missing` error
            # so the report makes the severity obvious.
            missing.append(field_name)
            if field_name in MANDATORY_FIELDS:
                errors.append(f"mandatory field missing: {field_name}")
            continue
        # Soft fields: present is enough (empty list accepted).
        if field_name in SOFT_FIELDS:
            continue
        # Present-but-empty: mandatory fields get a type-specific
        # error (not missing); non-mandatory fields go into missing.
        if _is_empty(ko[field_name]):
            if field_name in MANDATORY_FIELDS:
                pass  # the boundary_ok / applicability_ok check below will report it
            else:
                missing.append(field_name)

    # Mandatory fields that are PRESENT but invalid (empty list,
    # wrong type) get their own error message -- the field is
    # not "absent", it is "wrong".
    if "boundary" not in missing and "boundary" in ko:
        ok, msg = _boundary_ok(ko["boundary"])
        if not ok:
            errors.append(f"boundary: {msg}")
    if "applicability" not in missing and "applicability" in ko:
        ok, msg = _applicability_ok(ko["applicability"])
        if not ok:
            errors.append(f"applicability: {msg}")

    valid = not missing and not errors
    return ValidationResult(
        identity=identity_str,
        valid=valid,
        missing=missing,
        errors=errors,
    )


def validate_corpus(corpus_dir: Any) -> list[ValidationResult]:
    """Validate every .json file under `corpus_dir` (recursively).

    Files that do not parse as JSON are reported with identity
    "<unparseable>" and a single error message. Files that
    parse but have no `identity` use that same label.
    """

    import json
    from pathlib import Path

    out: list[ValidationResult] = []
    corpus_dir = Path(corpus_dir)
    if not corpus_dir.exists():
        return out
    for path in sorted(corpus_dir.rglob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            out.append(ValidationResult(
                identity="<unparseable>",
                valid=False,
                missing=list(REQUIRED_FIELDS),
                errors=[f"failed to parse {path.name}: {e}"],
            ))
            continue
        if not isinstance(data, dict):
            out.append(ValidationResult(
                identity="<non-dict>",
                valid=False,
                missing=list(REQUIRED_FIELDS),
                errors=[f"{path.name}: top-level value is not a dict"],
            ))
            continue
        result = validate_knowledge_object(data)
        out.append(result)
    return out


__all__ = [
    "REQUIRED_FIELDS",
    "MANDATORY_FIELDS",
    "SOFT_FIELDS",
    "ValidationResult",
    "validate_knowledge_object",
    "validate_corpus",
]