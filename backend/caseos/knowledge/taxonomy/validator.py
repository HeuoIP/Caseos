"""Knowledge Taxonomy Validator V1 (Sprint 23.1-C).

The validator is the **runtime guard** that enforces the
schema on both ``Taxonomy`` and ``TaxonomyNode`` instances.
It is stateless: every call is a pure function of the input.

Single-record checks (Taxonomy):

    T1  taxonomy_id is a non-empty string
    T2  version >= 1
    T3  name is a non-empty string
    T4  description is a non-empty string
    T5  taxonomy_type is in TAXONOMY_TYPE_ALLOW_LIST
    T6  root_node_ids is a list (may be empty)

Single-record checks (TaxonomyNode):

    N1  node_id is a non-empty string
    N2  version >= 1
    N3  label is a non-empty string
    N4  description is a non-empty string
    N5  node_type is in NODE_TYPE_ALLOW_LIST
    N6  parent_node_id, when present, is a non-empty
        string and must not equal node_id (no self-ref)
    N7  depth >= 1
    N8  path, when non-empty, must contain only
        non-empty strings

Cross-record checks (require the optional registry):

    C1  taxonomy_id is unique within the registry
    C2  node_id is unique within the registry
    C3  every Taxonomy.root_node_ids entry must refer to
        a node that exists in the registry

The validator returns a ``TaxonomyValidationResult`` with
a boolean verdict and a tuple of human-readable error
messages.

Architecture boundary (Sprint 23.1-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.taxonomy (sibling modules)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Iterable, Optional, Tuple, Union

from .object import Taxonomy, TaxonomyNode
from .schema import (
    FIELD_TYPES,
    NODE_FIELD_TYPES,
    NODE_REQUIRED_FIELDS,
    NODE_TYPE_ALLOW_LIST,
    REQUIRED_FIELDS,
    TAXONOMY_TYPE_ALLOW_LIST,
    VERSION_POLICY,
)


@dataclasses.dataclass(frozen=True)
class TaxonomyValidationResult:
    """The outcome of a ``TaxonomyValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: a tuple of human-readable error messages.
            Empty when ``valid`` is True.
        target_kind: "taxonomy" | "node"
    """

    valid: bool
    errors: Tuple[str, ...] = ()
    target_kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class TaxonomyValidator:
    """Stateless validator. ``validate`` is a pure function."""

    def validate(
        self,
        target: Optional[Union[Taxonomy, TaxonomyNode]],
        *,
        existing_taxonomies: Optional[Iterable[Taxonomy]] = None,
        existing_nodes: Optional[Iterable[TaxonomyNode]] = None,
    ) -> TaxonomyValidationResult:
        if target is None:
            return TaxonomyValidationResult(
                valid=False,
                errors=("target is None",),
                target_kind="",
            )

        # Use duck-typing so test fakes (plain objects
        # with the right attributes) can be validated.
        if hasattr(target, "node_id") and hasattr(target, "label"):
            return self._validate_node(
                target,
                existing_nodes=existing_nodes,
            )
        if hasattr(target, "taxonomy_id") and hasattr(target, "name"):
            return self._validate_taxonomy(
                target,
                existing_taxonomies=existing_taxonomies,
                existing_nodes=existing_nodes,
            )
        return TaxonomyValidationResult(
            valid=False,
            errors=(
                "target must be a Taxonomy or TaxonomyNode; got "
                + type(target).__name__,
            ),
            target_kind="",
        )

    # --------------------------------------------------------------
    # Taxonomy
    # --------------------------------------------------------------

    def _validate_taxonomy(
        self,
        taxonomy: Taxonomy,
        *,
        existing_taxonomies: Optional[Iterable[Taxonomy]],
        existing_nodes: Optional[Iterable[TaxonomyNode]],
    ) -> TaxonomyValidationResult:
        errors: list[str] = []

        # T1
        if not _is_nonempty_str(getattr(taxonomy, "taxonomy_id", "")):
            errors.append("taxonomy_id must be a non-empty string")

        # T2 -- version policy
        version = getattr(taxonomy, "version", None)
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

        # T3
        if not _is_nonempty_str(getattr(taxonomy, "name", "")):
            errors.append("name must be a non-empty string")

        # T4
        if not _is_nonempty_str(getattr(taxonomy, "description", "")):
            errors.append("description must be a non-empty string")

        # T5
        taxonomy_type = getattr(taxonomy, "taxonomy_type", None)
        if not _is_nonempty_str(taxonomy_type):
            errors.append("taxonomy_type must be a non-empty string")
        elif taxonomy_type not in TAXONOMY_TYPE_ALLOW_LIST:
            errors.append(
                "taxonomy_type not in V1 allow-list: "
                + repr(taxonomy_type)
                + " (allowed: "
                + ", ".join(sorted(TAXONOMY_TYPE_ALLOW_LIST))
                + ")"
            )

        # T6
        root_node_ids = getattr(taxonomy, "root_node_ids", None)
        if root_node_ids is None:
            errors.append("root_node_ids must be a list (may be empty)")
        elif not isinstance(root_node_ids, (list, tuple)):
            errors.append(
                "root_node_ids must be a list; got "
                + type(root_node_ids).__name__
            )
        else:
            for rid in root_node_ids:
                if not _is_nonempty_str(rid):
                    errors.append(
                        "root_node_ids entries must be non-empty strings"
                    )
                    break

        # Required fields + type safety
        for fname in REQUIRED_FIELDS:
            if not hasattr(taxonomy, fname):
                errors.append("missing required field: " + fname)
        for fname, accepted in FIELD_TYPES.items():
            if not hasattr(taxonomy, fname):
                continue
            value = getattr(taxonomy, fname)
            if not isinstance(value, accepted):
                errors.append(
                    "field " + fname
                    + " has wrong type: expected one of "
                    + ", ".join(t.__name__ for t in accepted)
                    + "; got " + type(value).__name__
                )

        # Cross-record checks
        if existing_taxonomies is not None:
            for other in existing_taxonomies:
                if (
                    hasattr(other, "taxonomy_id")
                    and other.taxonomy_id == taxonomy.taxonomy_id
                ):
                    errors.append(
                        "taxonomy_id is not unique in the registry: "
                        + repr(taxonomy.taxonomy_id)
                    )
                    break

        if existing_nodes is not None and isinstance(
            root_node_ids, (list, tuple)
        ):
            node_ids = {
                n.node_id
                for n in existing_nodes
                if hasattr(n, "node_id")
            }
            for rid in root_node_ids:
                if _is_nonempty_str(rid) and rid not in node_ids:
                    errors.append(
                        "root_node_ids entry "
                        + repr(rid)
                        + " does not refer to any registered node"
                    )
                    break

        return TaxonomyValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            target_kind="taxonomy",
        )

    # --------------------------------------------------------------
    # TaxonomyNode
    # --------------------------------------------------------------

    def _validate_node(
        self,
        node: TaxonomyNode,
        *,
        existing_nodes: Optional[Iterable[TaxonomyNode]],
    ) -> TaxonomyValidationResult:
        errors: list[str] = []

        # N1
        if not _is_nonempty_str(getattr(node, "node_id", "")):
            errors.append("node_id must be a non-empty string")

        # N2 -- version policy
        version = getattr(node, "version", None)
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

        # N3
        if not _is_nonempty_str(getattr(node, "label", "")):
            errors.append("label must be a non-empty string")

        # N4
        if not _is_nonempty_str(getattr(node, "description", "")):
            errors.append("description must be a non-empty string")

        # N5
        node_type = getattr(node, "node_type", None)
        if not _is_nonempty_str(node_type):
            errors.append("node_type must be a non-empty string")
        elif node_type not in NODE_TYPE_ALLOW_LIST:
            errors.append(
                "node_type not in V1 allow-list: "
                + repr(node_type)
                + " (allowed: "
                + ", ".join(sorted(NODE_TYPE_ALLOW_LIST))
                + ")"
            )

        # N6 -- parent_node_id
        parent_node_id = getattr(node, "parent_node_id", None)
        if parent_node_id is not None:
            if not _is_nonempty_str(parent_node_id):
                errors.append(
                    "parent_node_id, when present, must be a non-empty string"
                )
            elif parent_node_id == node.node_id:
                errors.append(
                    "parent_node_id must not equal node_id "
                    "(self-reference forbidden)"
                )

        # N7 -- depth
        depth = getattr(node, "depth", None)
        if not isinstance(depth, int) or isinstance(depth, bool):
            errors.append(
                "depth must be an int; got " + type(depth).__name__
            )
        elif depth < 1:
            errors.append(
                "depth must be >= 1; got " + str(depth)
            )

        # N8 -- path contains non-empty strings
        path = getattr(node, "path", None)
        if path is not None:
            if not isinstance(path, (list, tuple)):
                errors.append(
                    "path must be a list; got " + type(path).__name__
                )
            else:
                for entry in path:
                    if not _is_nonempty_str(entry):
                        errors.append(
                            "path entries must be non-empty strings"
                        )
                        break

        # Required fields + type safety
        for fname in NODE_REQUIRED_FIELDS:
            if not hasattr(node, fname):
                errors.append("missing required field: " + fname)
        for fname, accepted in NODE_FIELD_TYPES.items():
            if not hasattr(node, fname):
                continue
            value = getattr(node, fname)
            if not isinstance(value, accepted):
                errors.append(
                    "field " + fname
                    + " has wrong type: expected one of "
                    + ", ".join(t.__name__ for t in accepted)
                    + "; got " + type(value).__name__
                )

        # Cross-record checks
        if existing_nodes is not None:
            for other in existing_nodes:
                if (
                    hasattr(other, "node_id")
                    and other.node_id == node.node_id
                ):
                    errors.append(
                        "node_id is not unique in the registry: "
                        + repr(node.node_id)
                    )
                    break

        return TaxonomyValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
            target_kind="node",
        )


__all__ = [
    "TaxonomyValidator",
    "TaxonomyValidationResult",
]
