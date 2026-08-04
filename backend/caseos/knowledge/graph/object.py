"""Knowledge Graph Validation Object Schemas V1 (Sprint 23.2-A).

This module declares three frozen dataclasses that
constitute the runtime contract:

    GraphValidationRequest   -- input bundle
    GraphIssue               -- single inconsistency
    GraphValidationResult    -- output bundle

GraphValidationRequest fields:

    request_id           unique identifier
    knowledge_object     the KO being validated (or any
                         object with knowledge_id + version)
    bindings             list of KODomainBinding records
                         (each must expose knowledge_object_id
                         and domain_id via duck-typing)
    domains              list of KnowledgeDomain records
                         (each must expose domain_id)
    taxonomies           list of Taxonomy records (each must
                         expose taxonomy_id)
    taxonomy_nodes       list of TaxonomyNode records (each
                         must expose node_id)
    attributes           list of KnowledgeAttribute records
                         (each must expose attribute_id,
                         name, data_type, required,
                         allowed_taxonomy_id,
                         allowed_node_ids)
    ko_attribute_values  dict mapping attribute name -> KO
                         field value (raw, not yet type-coerced)
    created_at           ISO timestamp (datetime)

The request is **immutable**. Collection fields
(`bindings`, `domains`, `taxonomies`, `taxonomy_nodes`,
`attributes`, `ko_attribute_values`) are deep-copied in
``__post_init__`` so caller mutations cannot leak into
the runtime's internal state.

GraphIssue fields:

    issue_id         unique identifier
    rule_id          the rule that triggered (e.g. "G1")
    severity         error | warning | info
    target_kind      knowledge_object | binding | domain |
                     attribute | taxonomy_node
    target_id        id of the entity that violated
    field_name       optional: which field is wrong
    message          human-readable explanation
    created_at       ISO timestamp (datetime)

The issue is **immutable**.

GraphValidationResult fields:

    request_id             echoes the request id
    knowledge_object_id    echoes the KO id
    success                True iff no issues with
                           severity=error were emitted
    issues                 tuple of all GraphIssue records
    errors                 tuple of issues with severity=error
    warnings               tuple of issues with severity=warning
    created_at             ISO timestamp (datetime)

The result is **immutable**.

Architecture boundary (Sprint 23.2-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * caseos.knowledge.domain (sibling Domain schema)
        * caseos.knowledge.binding (sibling Binding)
        * caseos.knowledge.taxonomy (sibling Taxonomy)
        * caseos.knowledge.attribute (sibling Attribute)
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, FrozenSet, Optional, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return prefix + "-" + str(uuid.uuid4())


SEVERITY_ALLOW_LIST: FrozenSet[str] = frozenset({
    "error",
    "warning",
    "info",
})

TARGET_KIND_ALLOW_LIST: FrozenSet[str] = frozenset({
    "knowledge_object",
    "binding",
    "domain",
    "attribute",
    "taxonomy",
    "taxonomy_node",
})


class GraphIssueError(ValueError):
    """Base error for the knowledge.graph package."""


class GraphValidationError(GraphIssueError):
    """Raised by the runtime when an invariant is violated
    by the *runtime itself* (not by the data being
    validated). For example, when a request bundle is
    missing required components.
    """


@dataclass(frozen=True)
class GraphValidationRequest:
    """A single graph validation call. Immutable."""

    request_id: str
    knowledge_object: Any
    bindings: list = field(default_factory=list)
    domains: list = field(default_factory=list)
    taxonomies: list = field(default_factory=list)
    taxonomy_nodes: list = field(default_factory=list)
    attributes: list = field(default_factory=list)
    ko_attribute_values: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Defensive deep-copy of every collection field.
        for fname in (
            "bindings", "domains", "taxonomies",
            "taxonomy_nodes", "attributes",
        ):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, copy.deepcopy(raw))
            elif isinstance(raw, tuple):
                object.__setattr__(
                    self, fname, copy.deepcopy(list(raw)),
                )
        if isinstance(self.ko_attribute_values, dict):
            object.__setattr__(
                self, "ko_attribute_values",
                copy.deepcopy(self.ko_attribute_values),
            )

        if not isinstance(self.request_id, str) or not self.request_id:
            raise GraphValidationError(
                "request_id must be a non-empty string"
            )
        if self.knowledge_object is None:
            raise GraphValidationError(
                "knowledge_object is required"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "request_id": self.request_id,
            "knowledge_object_id": _get_attr(
                self.knowledge_object, "knowledge_id", ""
            ),
            "ko_version": _get_attr(
                self.knowledge_object, "version", 0
            ),
            "bindings": [_safe_id(b) for b in self.bindings],
            "domains": [_safe_id(d) for d in self.domains],
            "taxonomies": [_safe_id(t) for t in self.taxonomies],
            "taxonomy_nodes": [_safe_id(n) for n in self.taxonomy_nodes],
            "attributes": [_safe_id(a) for a in self.attributes],
            "ko_attribute_values": _safe_dict(self.ko_attribute_values),
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(self.created_at, datetime)
                else self.created_at,
        }
        return out


@dataclass(frozen=True)
class GraphIssue:
    """A single inconsistency emitted by the validator.

    Severity levels:

        * ``error`` -- the rule failed in a way that
          prevents the KO from being valid. ``success=False``
          on the parent ``GraphValidationResult``.
        * ``warning`` -- the rule reports a soft issue that
          a future Sprint may flag for review but does
          not invalidate the KO.
        * ``info`` -- diagnostic information only.

    The issue is immutable.
    """

    issue_id: str
    rule_id: str
    severity: str
    target_kind: str
    target_id: str
    field_name: Optional[str]
    message: str
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not isinstance(self.issue_id, str) or not self.issue_id:
            raise GraphValidationError(
                "issue_id must be a non-empty string"
            )
        if self.severity not in SEVERITY_ALLOW_LIST:
            raise GraphValidationError(
                "severity must be one of "
                + ", ".join(sorted(SEVERITY_ALLOW_LIST))
                + "; got " + repr(self.severity)
            )
        if self.target_kind not in TARGET_KIND_ALLOW_LIST:
            raise GraphValidationError(
                "target_kind must be one of "
                + ", ".join(sorted(TARGET_KIND_ALLOW_LIST))
                + "; got " + repr(self.target_kind)
            )

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


@dataclass(frozen=True)
class GraphValidationResult:
    """The outcome of a ``KnowledgeGraphValidator.validate`` call.

    The runtime NEVER mutates any of the supplied graph
    components. ``success=True`` iff no ``severity=error``
    issue was emitted. ``warnings`` and ``info`` issues
    do not invalidate the KO.
    """

    request_id: str
    knowledge_object_id: str
    success: bool
    issues: Tuple[GraphIssue, ...] = ()
    errors: Tuple[GraphIssue, ...] = ()
    warnings: Tuple[GraphIssue, ...] = ()
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        out["issues"] = [i.to_dict() for i in self.issues]
        out["errors"] = [i.to_dict() for i in self.errors]
        out["warnings"] = [i.to_dict() for i in self.warnings]
        return out


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _get_attr(obj: Any, name: str, default: Any) -> Any:
    if obj is None:
        return default
    return getattr(obj, name, default)


def _safe_id(obj: Any) -> str:
    """Best-effort id extraction for duck-typed records."""
    for fname in (
        "binding_id", "domain_id", "taxonomy_id",
        "node_id", "attribute_id", "knowledge_id",
    ):
        v = getattr(obj, fname, None)
        if isinstance(v, str) and v:
            return v
    return ""


def _safe_dict(d: Any) -> dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    return {str(k): v for k, v in d.items()}


def _new_issue_id() -> str:
    return _new_id("iss")


__all__ = [
    "GraphIssue",
    "GraphIssueError",
    "GraphValidationRequest",
    "GraphValidationResult",
    "GraphValidationError",
    "SEVERITY_ALLOW_LIST",
    "TARGET_KIND_ALLOW_LIST",
]
