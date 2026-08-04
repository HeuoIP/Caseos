"""Binding Validator V1 (Sprint 23.1-B).

The validator is the **runtime guard** that enforces the
``KODomainBindingSchema`` on a ``KODomainBinding``
instance. It is stateless: every call is a pure function of
the input.

Single-record checks (Sprint 23.1-B spec):

    B1  binding_id is a non-empty string
    B2  version >= 1
    B3  knowledge_object_id is a non-empty string
    B4  knowledge_object_version >= 1
    B5  domain_id is a non-empty string
    B6  binding_type is in BINDING_TYPE_ALLOW_LIST
    B7  priority >= 1
    B8  membership_reason is a non-empty string

Cross-record checks (require the optional ``registry``
argument):

    C1  binding_id is unique within the registry
    C2  at most one ``primary`` binding per
        ``knowledge_object_id`` exists in the registry

The validator returns a ``BindingValidationResult`` with a
boolean verdict and a tuple of human-readable error
messages.

Architecture boundary (Sprint 23.1-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.binding (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable, Optional, Tuple

from .object import KODomainBinding
from .schema import (
    BINDING_TYPE_ALLOW_LIST,
    BINDING_VERSION_POLICY,
    FIELD_TYPES,
    REQUIRED_FIELDS,
)


@dataclasses.dataclass(frozen=True)
class BindingValidationResult:
    """The outcome of a ``BindingValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: a tuple of human-readable error messages.
            Empty when ``valid`` is True.
    """

    valid: bool
    errors: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class BindingValidator:
    """Stateless validator. ``validate`` is a pure function.

    The optional ``existing_bindings`` argument enables
    cross-record checks (uniqueness, primary-binding
    uniqueness). When not supplied, only single-record
    checks run.
    """

    def validate(
        self,
        binding: Optional[KODomainBinding],
        *,
        existing_bindings: Optional[Iterable[KODomainBinding]] = None,
    ) -> BindingValidationResult:
        errors: list[str] = []

        if binding is None:
            return BindingValidationResult(
                valid=False,
                errors=("binding is None",),
            )

        # B1
        if not _is_nonempty_str(getattr(binding, "binding_id", "")):
            errors.append("binding_id must be a non-empty string")

        # B2 -- version policy: must be a positive integer.
        version = getattr(binding, "version", None)
        min_version = int(BINDING_VERSION_POLICY.get("min_version", 1))
        version_type = BINDING_VERSION_POLICY.get("version_type", int)
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

        # B3
        if not _is_nonempty_str(getattr(binding, "knowledge_object_id", "")):
            errors.append("knowledge_object_id must be a non-empty string")

        # B4 -- knowledge_object_version >= 1
        ko_version = getattr(binding, "knowledge_object_version", None)
        if not isinstance(ko_version, int) or isinstance(ko_version, bool):
            errors.append(
                "knowledge_object_version must be an int; got "
                + type(ko_version).__name__
            )
        elif ko_version < 1:
            errors.append(
                "knowledge_object_version must be >= 1; got "
                + str(ko_version)
            )

        # B5
        if not _is_nonempty_str(getattr(binding, "domain_id", "")):
            errors.append("domain_id must be a non-empty string")

        # B6 -- binding_type must be in the allow-list
        binding_type = getattr(binding, "binding_type", None)
        if not _is_nonempty_str(binding_type):
            errors.append("binding_type must be a non-empty string")
        elif binding_type not in BINDING_TYPE_ALLOW_LIST:
            errors.append(
                "binding_type not in V1 allow-list: "
                + repr(binding_type)
                + " (allowed: "
                + ", ".join(sorted(BINDING_TYPE_ALLOW_LIST))
                + ")"
            )

        # B7 -- priority >= 1
        priority = getattr(binding, "priority", None)
        if not isinstance(priority, int) or isinstance(priority, bool):
            errors.append(
                "priority must be an int; got "
                + type(priority).__name__
            )
        elif priority < 1:
            errors.append(
                "priority must be >= 1; got " + str(priority)
            )

        # B8 -- membership_reason must be a non-empty string
        if not _is_nonempty_str(getattr(binding, "membership_reason", "")):
            errors.append("membership_reason must be a non-empty string")

        # Required fields: every REQUIRED_FIELDS entry must be
        # present (i.e. accessible via getattr).
        for fname in REQUIRED_FIELDS:
            if not hasattr(binding, fname):
                errors.append("missing required field: " + fname)

        # Type safety: each present field must satisfy FIELD_TYPES.
        for fname, accepted in FIELD_TYPES.items():
            if not hasattr(binding, fname):
                continue
            value = getattr(binding, fname)
            if not isinstance(value, accepted):
                errors.append(
                    "field " + fname
                    + " has wrong type: expected one of "
                    + ", ".join(t.__name__ for t in accepted)
                    + "; got " + type(value).__name__
                )

        # Cross-record checks (optional)
        if existing_bindings is not None:
            existing = list(existing_bindings)
            for other in existing:
                # C1 -- binding_id uniqueness
                if (
                    isinstance(other, KODomainBinding)
                    and other.binding_id == binding.binding_id
                ):
                    errors.append(
                        "binding_id is not unique in the registry: "
                        + repr(binding.binding_id)
                    )
                    break

            # C2 -- at most one primary per knowledge_object_id
            if binding.binding_type == "primary":
                primary_count = sum(
                    1
                    for other in existing
                    if isinstance(other, KODomainBinding)
                    and other.knowledge_object_id
                    == binding.knowledge_object_id
                    and other.binding_type == "primary"
                )
                if primary_count > 0:
                    errors.append(
                        "knowledge_object_id "
                        + repr(binding.knowledge_object_id)
                        + " already has a primary binding; "
                        "only one primary per KO is allowed"
                    )

        return BindingValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
        )


__all__ = [
    "BindingValidator",
    "BindingValidationResult",
]
