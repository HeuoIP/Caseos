"""Knowledge Attribute Validator V1 (Sprint 23.1-D).

The validator is the **runtime guard** that enforces the
schema on a ``KnowledgeAttribute`` instance. It is
stateless: every call is a pure function of the input.

Single-record checks:

    A1  attribute_id is a non-empty string
    A2  version >= 1
    A3  name is a non-empty string
    A4  description is a non-empty string
    A5  attribute_type is in ATTRIBUTE_TYPE_ALLOW_LIST
    A6  data_type is in DATA_TYPE_ALLOW_LIST
    A7  cardinality is in CARDINALITY_ALLOW_LIST
    A8  required is a bool
    A9  default_value, when present, is a non-empty string
    A10 min_value <= max_value when both are numbers
    A11 for data_type=enum, allowed_node_ids is non-empty
    A12 cardinality=set requires allowed_node_ids to be
        non-empty (otherwise the constraint is meaningless)

Cross-record checks (require the optional registries):

    AC1 attribute_id is unique within the attribute registry
    AC2 allowed_taxonomy_id, when present, must exist in
        the taxonomy registry

The validator returns an ``AttributeValidationResult``
with a boolean verdict and a tuple of human-readable error
messages.

Architecture boundary (Sprint 23.1-D spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.attribute (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable, Optional, Tuple

from .object import KnowledgeAttribute
from .schema import (
    ATTRIBUTE_TYPE_ALLOW_LIST,
    CARDINALITY_ALLOW_LIST,
    DATA_TYPE_ALLOW_LIST,
    FIELD_TYPES,
    REQUIRED_FIELDS,
    VERSION_POLICY,
)


@dataclasses.dataclass(frozen=True)
class AttributeValidationResult:
    """The outcome of a ``KnowledgeAttributeValidator.validate`` call.

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


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class KnowledgeAttributeValidator:
    """Stateless validator. ``validate`` is a pure function.

    Cross-record checks are activated by supplying
    ``existing_attributes`` and / or ``existing_taxonomies``.
    """

    def validate(
        self,
        attribute: Optional[KnowledgeAttribute],
        *,
        existing_attributes: Optional[Iterable[Any]] = None,
        existing_taxonomies: Optional[Iterable[Any]] = None,
    ) -> AttributeValidationResult:
        errors: list[str] = []

        if attribute is None:
            return AttributeValidationResult(
                valid=False,
                errors=("attribute is None",),
            )

        # A1
        if not _is_nonempty_str(getattr(attribute, "attribute_id", "")):
            errors.append("attribute_id must be a non-empty string")

        # A2 -- version policy
        version = getattr(attribute, "version", None)
        min_version = int(VERSION_POLICY.get("min_version", 1))
        version_type = VERSION_POLICY.get("version_type", int)
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

        # A3
        if not _is_nonempty_str(getattr(attribute, "name", "")):
            errors.append("name must be a non-empty string")

        # A4
        if not _is_nonempty_str(getattr(attribute, "description", "")):
            errors.append("description must be a non-empty string")

        # A5 -- attribute_type
        attribute_type = getattr(attribute, "attribute_type", None)
        if not _is_nonempty_str(attribute_type):
            errors.append("attribute_type must be a non-empty string")
        elif attribute_type not in ATTRIBUTE_TYPE_ALLOW_LIST:
            errors.append(
                "attribute_type not in V1 allow-list: "
                + repr(attribute_type)
                + " (allowed: "
                + ", ".join(sorted(ATTRIBUTE_TYPE_ALLOW_LIST))
                + ")"
            )

        # A6 -- data_type
        data_type = getattr(attribute, "data_type", None)
        if not _is_nonempty_str(data_type):
            errors.append("data_type must be a non-empty string")
        elif data_type not in DATA_TYPE_ALLOW_LIST:
            errors.append(
                "data_type not in V1 allow-list: "
                + repr(data_type)
                + " (allowed: "
                + ", ".join(sorted(DATA_TYPE_ALLOW_LIST))
                + ")"
            )

        # A7 -- cardinality
        cardinality = getattr(attribute, "cardinality", None)
        if not _is_nonempty_str(cardinality):
            errors.append("cardinality must be a non-empty string")
        elif cardinality not in CARDINALITY_ALLOW_LIST:
            errors.append(
                "cardinality not in V1 allow-list: "
                + repr(cardinality)
                + " (allowed: "
                + ", ".join(sorted(CARDINALITY_ALLOW_LIST))
                + ")"
            )

        # A8 -- required is a bool
        required = getattr(attribute, "required", None)
        if not isinstance(required, bool):
            errors.append(
                "required must be a bool; got " + type(required).__name__
            )

        # A9 -- default_value, when present, must be a non-empty string
        default_value = getattr(attribute, "default_value", None)
        if default_value is not None and not _is_nonempty_str(default_value):
            errors.append(
                "default_value, when present, must be a non-empty string"
            )

        # A10 -- min_value <= max_value
        min_value = getattr(attribute, "min_value", None)
        max_value = getattr(attribute, "max_value", None)
        if _is_number(min_value) and _is_number(max_value):
            if min_value > max_value:
                errors.append(
                    "min_value (" + str(min_value)
                    + ") must be <= max_value ("
                    + str(max_value) + ")"
                )

        # A11 -- for data_type=enum, allowed_node_ids non-empty
        allowed_node_ids = getattr(attribute, "allowed_node_ids", None)
        if data_type == "enum":
            if not isinstance(allowed_node_ids, (list, tuple)):
                errors.append(
                    "data_type=enum requires allowed_node_ids to be a list"
                )
            elif len(allowed_node_ids) == 0:
                errors.append(
                    "data_type=enum requires allowed_node_ids to be "
                    "non-empty"
                )
            else:
                for nid in allowed_node_ids:
                    if not _is_nonempty_str(nid):
                        errors.append(
                            "allowed_node_ids entries must be non-empty "
                            "strings"
                        )
                        break

        # A12 -- cardinality=set requires allowed_node_ids non-empty
        if cardinality == "set" and isinstance(
            allowed_node_ids, (list, tuple)
        ) and len(allowed_node_ids) == 0:
            errors.append(
                "cardinality=set requires allowed_node_ids to be non-empty"
            )

        # Required fields + type safety
        for fname in REQUIRED_FIELDS:
            if not hasattr(attribute, fname):
                errors.append("missing required field: " + fname)
        for fname, accepted in FIELD_TYPES.items():
            if not hasattr(attribute, fname):
                continue
            value = getattr(attribute, fname)
            if not isinstance(value, accepted):
                errors.append(
                    "field " + fname
                    + " has wrong type: expected one of "
                    + ", ".join(t.__name__ for t in accepted)
                    + "; got " + type(value).__name__
                )

        # Cross-record checks
        if existing_attributes is not None:
            for other in existing_attributes:
                if (
                    hasattr(other, "attribute_id")
                    and other.attribute_id == attribute.attribute_id
                ):
                    errors.append(
                        "attribute_id is not unique in the registry: "
                        + repr(attribute.attribute_id)
                    )
                    break

        if existing_taxonomies is not None and getattr(
            attribute, "allowed_taxonomy_id", None
        ) is not None:
            target_taxonomy_id = attribute.allowed_taxonomy_id
            tax_ids = {
                t.taxonomy_id
                for t in existing_taxonomies
                if hasattr(t, "taxonomy_id")
            }
            if target_taxonomy_id not in tax_ids:
                errors.append(
                    "allowed_taxonomy_id "
                    + repr(target_taxonomy_id)
                    + " does not refer to any registered taxonomy"
                )

        return AttributeValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
        )


__all__ = [
    "KnowledgeAttributeValidator",
    "AttributeValidationResult",
]
