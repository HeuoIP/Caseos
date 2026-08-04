"""Knowledge Domain Validator V1 (Sprint 23.1-A).

The validator is the **runtime guard** that enforces the
``KnowledgeDomainSchema`` on a ``KnowledgeDomain`` instance.
It is stateless: every call is a pure function of the input.

Checks (Sprint 23.1-A spec):

    Identity            domain_id must be a non-empty string
    Version             version >= 1 (V1 first_version)
    Required Fields     every REQUIRED_FIELDS entry must be
                        present in the dataclass
    Domain Type         domain_type must be in
                        DOMAIN_TYPE_ALLOW_LIST
    Type Safety         each field must satisfy FIELD_TYPES
    JSON Safety         collection fields must contain only
                        JSON-safe scalars; ``None`` is also
                        acceptable (treated as "absent")
    Hierarchy           parent_domain_id, when non-None,
                        must be a non-empty string and must
                        not equal the domain's own id
                        (no self-reference)

The validator returns a ``DomainValidationResult`` with a
boolean verdict and a tuple of human-readable error messages.
The dataclass's own ``__post_init__`` runs a subset of these
checks (identity + version) and raises on failure; the
validator is the **defence-in-depth** layer that also
surfaces field-level errors.

Architecture boundary (Sprint 23.1-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.domain (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Optional, Tuple

from .object import KnowledgeDomain
from .schema import (
    DOMAIN_TYPE_ALLOW_LIST,
    DOMAIN_VERSION_POLICY,
    FIELD_TYPES,
    REQUIRED_FIELDS,
)


@dataclasses.dataclass(frozen=True)
class DomainValidationResult:
    """The outcome of a ``KnowledgeDomainValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: a tuple of human-readable error messages.
            Empty when ``valid`` is True.
    """

    valid: bool
    errors: Tuple[str, ...] = ()


def _is_json_safe_scalar(value: Any) -> bool:
    """True iff ``value`` round-trips through ``json.dumps``."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def _is_json_safe_collection(value: Any) -> bool:
    """True iff ``value`` is a list/tuple whose elements are
    JSON-safe (recursively). ``None`` is treated as safe."""
    if value is None:
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_json_safe_scalar(v) for v in value)
    return _is_json_safe_scalar(value)


class KnowledgeDomainValidator:
    """Stateless validator. ``validate`` is a pure function."""

    def validate(
        self,
        obj: Optional[KnowledgeDomain],
    ) -> DomainValidationResult:
        """Validate a ``KnowledgeDomain`` against the V1 schema."""
        errors: list[str] = []

        if obj is None:
            return DomainValidationResult(
                valid=False,
                errors=("object is None",),
            )

        # Identity: domain_id must be a non-empty string.
        domain_id = getattr(obj, "domain_id", None)
        if not isinstance(domain_id, str) or not domain_id.strip():
            errors.append("domain_id must be a non-empty string")

        # Version policy: must be a positive integer.
        version = getattr(obj, "version", None)
        min_version = int(DOMAIN_VERSION_POLICY.get("min_version", 1))
        version_type = DOMAIN_VERSION_POLICY.get("version_type", int)
        if not isinstance(version, version_type):
            errors.append(
                "version must be "
                + getattr(version_type, "__name__", str(version_type))
                + "; got " + type(version).__name__
            )
        elif version < min_version:
            errors.append(
                "version must be >= " + str(min_version)
                + "; got " + str(version)
            )

        # Domain type allow-list.
        domain_type = getattr(obj, "domain_type", None)
        if not isinstance(domain_type, str) or not domain_type:
            errors.append("domain_type must be a non-empty string")
        elif domain_type not in DOMAIN_TYPE_ALLOW_LIST:
            errors.append(
                "domain_type not in V1 allow-list: "
                + repr(domain_type)
                + " (allowed: " + ", ".join(sorted(DOMAIN_TYPE_ALLOW_LIST)) + ")"
            )

        # Required fields: every REQUIRED_FIELDS entry must be
        # present (i.e. accessible via getattr).
        for fname in REQUIRED_FIELDS:
            if not hasattr(obj, fname):
                errors.append("missing required field: " + fname)

        # Type safety: each present field must satisfy FIELD_TYPES.
        for fname, accepted in FIELD_TYPES.items():
            if not hasattr(obj, fname):
                continue
            value = getattr(obj, fname)
            if not isinstance(value, accepted):
                errors.append(
                    "field " + fname
                    + " has wrong type: expected one of "
                    + ", ".join(t.__name__ for t in accepted)
                    + "; got " + type(value).__name__
                )

        # JSON safety: collection fields must be JSON-safe.
        for fname in (
            "scope_tags",
            "allowed_knowledge_types",
            "boundary_rules",
            "principle_rules",
        ):
            if not hasattr(obj, fname):
                continue
            value = getattr(obj, fname)
            if not _is_json_safe_collection(value):
                errors.append(
                    "field " + fname + " is not JSON-safe"
                )

        # Hierarchy invariant: parent_domain_id, when present,
        # must be a non-empty string and must not equal the
        # domain's own id.
        if hasattr(obj, "parent_domain_id"):
            parent = getattr(obj, "parent_domain_id", None)
            if parent is not None:
                if not isinstance(parent, str) or not parent.strip():
                    errors.append(
                        "parent_domain_id, when present, "
                        "must be a non-empty string"
                    )
                elif isinstance(domain_id, str) and parent == domain_id:
                    errors.append(
                        "parent_domain_id must not equal domain_id "
                        "(self-reference forbidden)"
                    )

        return DomainValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
        )


__all__ = ["KnowledgeDomainValidator", "DomainValidationResult"]
