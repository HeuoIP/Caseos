"""Knowledge Graph Validator V1 (Sprint 23.2-A).

The ``KnowledgeGraphValidator`` is the **cross-layer
consistency checker** for the CaseOS knowledge graph. It
reads the V1 data contracts supplied via a
``GraphValidationRequest`` and emits a structured
``GraphValidationResult``.

Hard invariants (Sprint 23.2-A spec):

    * The validator NEVER mutates any of the supplied
      graph components.
    * The validator NEVER imports from any intelligence
      module or Retrieval.
    * The validator NEVER introduces auto-learning, LLM,
      or embedding logic.
    * The validator is deterministic: same input -> same
      output.

V1 validation rules:

    G1  KO.category must be in bound Domain's
        allowed_knowledge_types (when the bound Domain
        declares a non-empty list)
    G2  For each Attribute bound to the KO, if
        ``required=True`` the KO's field value must exist
        and be non-empty
    G3  For each Attribute with ``data_type=enum``, the
        KO's field value must be in
        ``attribute.allowed_node_ids`` (when the list is
        non-empty)
    G4  For each Attribute with ``data_type=string`` and
        ``pattern`` set, the KO's value must match the
        pattern (substring match; not full regex)
    G5  For each Attribute with ``data_type=number``, the
        KO's value must be a number in
        ``[min_value, max_value]`` (when both bounds are
        set)
    G6  Each Binding must reference a Domain that is
        present in the request bundle
    G7  Each Attribute's ``allowed_taxonomy_id``, when
        set, must refer to a Taxonomy present in the
        request bundle
    G8  Each Binding's ``knowledge_object_id`` must equal
        the request's KO id

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

import re
from datetime import datetime, timezone
from typing import Any, List, Optional

from .object import (
    GraphIssue,
    GraphValidationRequest,
    GraphValidationResult,
    _new_id,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class KnowledgeGraphValidator:
    """Stateless cross-layer checker.

    Construction-time configuration:

        rule_set    optional override of the rule allow-list
                    (the V1 default is ``{G1, G2, ..., G8}``).
                    Disabled rules are silently skipped.

    The validator is a pure function of the
    ``GraphValidationRequest``. ``validate`` never mutates
    the request or any of the supplied graph components.
    """

    V1_RULES: frozenset = frozenset({
        "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8",
    })

    def __init__(
        self,
        *,
        rule_set: Optional[frozenset] = None,
    ) -> None:
        self.rule_set: frozenset = (
            rule_set if rule_set is not None else self.V1_RULES
        )

    # -------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------

    def validate(
        self,
        request: GraphValidationRequest,
    ) -> GraphValidationResult:
        """Run all enabled rules against ``request``.

        Returns a frozen ``GraphValidationResult``. ``success``
        is True iff no issue with ``severity=error`` was
        emitted.
        """
        issues: List[GraphIssue] = []

        # Collect lookup tables once.
        domains_by_id: dict = self._index_by(
            request.domains, "domain_id"
        )
        taxonomies_by_id: dict = self._index_by(
            request.taxonomies, "taxonomy_id"
        )
        nodes_by_id: dict = self._index_by(
            request.taxonomy_nodes, "node_id"
        )

        if "G1" in self.rule_set:
            self._rule_g1(request, domains_by_id, issues)

        if "G6" in self.rule_set:
            self._rule_g6(request, domains_by_id, issues)

        if "G7" in self.rule_set:
            self._rule_g7(request, taxonomies_by_id, issues)

        if "G8" in self.rule_set:
            self._rule_g8(request, issues)

        if "G2" in self.rule_set:
            self._rule_g2(request, issues)

        if "G3" in self.rule_set:
            self._rule_g3(request, issues)

        if "G4" in self.rule_set:
            self._rule_g4(request, issues)

        if "G5" in self.rule_set:
            self._rule_g5(request, issues)

        errors = tuple(
            i for i in issues if i.severity == "error"
        )
        warnings = tuple(
            i for i in issues if i.severity == "warning"
        )

        return GraphValidationResult(
            request_id=request.request_id,
            knowledge_object_id=_get_attr(
                request.knowledge_object, "knowledge_id", ""
            ),
            success=(len(errors) == 0),
            issues=tuple(issues),
            errors=errors,
            warnings=warnings,
            created_at=_now(),
        )

    # -------------------------------------------------------------
    # Rule G1: KO.category in Domain.allowed_knowledge_types
    # -------------------------------------------------------------

    def _rule_g1(
        self,
        request: GraphValidationRequest,
        domains_by_id: dict,
        issues: List[GraphIssue],
    ) -> None:
        ko_category = _get_attr(
            request.knowledge_object, "category", None
        )
        if not _is_nonempty_str(ko_category):
            return
        for binding in request.bindings:
            domain_id = _get_attr(binding, "domain_id", None)
            if not _is_nonempty_str(domain_id):
                continue
            domain = domains_by_id.get(domain_id)
            if domain is None:
                continue
            allowed = _get_attr(
                domain, "allowed_knowledge_types", []
            )
            if not isinstance(allowed, (list, tuple)) or len(allowed) == 0:
                continue
            if ko_category not in list(allowed):
                issues.append(self._mk_issue(
                    rule_id="G1",
                    severity="error",
                    target_kind="domain",
                    target_id=domain_id,
                    field_name="category",
                    message=(
                        "knowledge_object.category "
                        + repr(ko_category)
                        + " is not in domain.allowed_knowledge_types "
                        + repr(list(allowed))
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G2: required attribute must have a non-empty KO value
    # -------------------------------------------------------------

    def _rule_g2(
        self,
        request: GraphValidationRequest,
        issues: List[GraphIssue],
    ) -> None:
        for attr in request.attributes:
            attr_name = _get_attr(attr, "name", None)
            if not _is_nonempty_str(attr_name):
                continue
            required = bool(_get_attr(attr, "required", False))
            if not required:
                continue
            value = request.ko_attribute_values.get(attr_name, None)
            missing = value is None
            empty = isinstance(value, str) and not value.strip()
            if missing or empty:
                issues.append(self._mk_issue(
                    rule_id="G2",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name=attr_name,
                    message=(
                        "required attribute '"
                        + attr_name
                        + "' has no non-empty value in "
                        "ko_attribute_values"
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G3: enum value must be in attribute.allowed_node_ids
    # -------------------------------------------------------------

    def _rule_g3(
        self,
        request: GraphValidationRequest,
        issues: List[GraphIssue],
    ) -> None:
        for attr in request.attributes:
            if _get_attr(attr, "data_type", None) != "enum":
                continue
            attr_name = _get_attr(attr, "name", None)
            if not _is_nonempty_str(attr_name):
                continue
            allowed = _get_attr(
                attr, "allowed_node_ids", []
            )
            if not isinstance(allowed, (list, tuple)) or len(allowed) == 0:
                continue
            value = request.ko_attribute_values.get(attr_name, None)
            if value is None:
                # G2 already covers the required case.
                continue
            if value not in list(allowed):
                issues.append(self._mk_issue(
                    rule_id="G3",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name=attr_name,
                    message=(
                        "ko_attribute_values['"
                        + attr_name
                        + "'] = "
                        + repr(value)
                        + " is not in "
                        "attribute.allowed_node_ids "
                        + repr(list(allowed))
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G4: string value must match attribute.pattern (substring)
    # -------------------------------------------------------------

    def _rule_g4(
        self,
        request: GraphValidationRequest,
        issues: List[GraphIssue],
    ) -> None:
        for attr in request.attributes:
            if _get_attr(attr, "data_type", None) != "string":
                continue
            attr_name = _get_attr(attr, "name", None)
            if not _is_nonempty_str(attr_name):
                continue
            pattern = _get_attr(attr, "pattern", None)
            if not _is_nonempty_str(pattern):
                continue
            value = request.ko_attribute_values.get(attr_name, None)
            if not isinstance(value, str):
                continue
            try:
                if not re.search(pattern, value):
                    issues.append(self._mk_issue(
                        rule_id="G4",
                        severity="warning",
                        target_kind="attribute",
                        target_id=_get_attr(attr, "attribute_id", ""),
                        field_name=attr_name,
                        message=(
                            "ko_attribute_values['"
                            + attr_name
                            + "'] = "
                            + repr(value)
                            + " does not match pattern "
                            + repr(pattern)
                        ),
                    ))
            except re.error:
                # A bad pattern is a runtime contract issue,
                # not a graph issue. Emit an info note.
                issues.append(self._mk_issue(
                    rule_id="G4",
                    severity="info",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name=attr_name,
                    message=(
                        "attribute.pattern "
                        + repr(pattern)
                        + " is not a valid regex; G4 skipped"
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G5: number value must be in [min_value, max_value]
    # -------------------------------------------------------------

    def _rule_g5(
        self,
        request: GraphValidationRequest,
        issues: List[GraphIssue],
    ) -> None:
        for attr in request.attributes:
            if _get_attr(attr, "data_type", None) != "number":
                continue
            attr_name = _get_attr(attr, "name", None)
            if not _is_nonempty_str(attr_name):
                continue
            min_value = _get_attr(attr, "min_value", None)
            max_value = _get_attr(attr, "max_value", None)
            if not _is_number(min_value) and not _is_number(max_value):
                continue
            value = request.ko_attribute_values.get(attr_name, None)
            if not _is_number(value):
                if value is not None:
                    issues.append(self._mk_issue(
                        rule_id="G5",
                        severity="error",
                        target_kind="attribute",
                        target_id=_get_attr(attr, "attribute_id", ""),
                        field_name=attr_name,
                        message=(
                            "ko_attribute_values['"
                            + attr_name
                            + "'] is not a number; got "
                            + repr(value)
                        ),
                    ))
                continue
            if _is_number(min_value) and value < min_value:
                issues.append(self._mk_issue(
                    rule_id="G5",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name=attr_name,
                    message=(
                        "ko_attribute_values['"
                        + attr_name
                        + "'] = "
                        + str(value)
                        + " is below min_value "
                        + str(min_value)
                    ),
                ))
            if _is_number(max_value) and value > max_value:
                issues.append(self._mk_issue(
                    rule_id="G5",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name=attr_name,
                    message=(
                        "ko_attribute_values['"
                        + attr_name
                        + "'] = "
                        + str(value)
                        + " is above max_value "
                        + str(max_value)
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G6: Binding must reference an existing Domain
    # -------------------------------------------------------------

    def _rule_g6(
        self,
        request: GraphValidationRequest,
        domains_by_id: dict,
        issues: List[GraphIssue],
    ) -> None:
        for binding in request.bindings:
            domain_id = _get_attr(binding, "domain_id", None)
            if not _is_nonempty_str(domain_id):
                issues.append(self._mk_issue(
                    rule_id="G6",
                    severity="error",
                    target_kind="binding",
                    target_id=_get_attr(binding, "binding_id", ""),
                    field_name="domain_id",
                    message=(
                        "binding.domain_id is missing or empty"
                    ),
                ))
                continue
            if domain_id not in domains_by_id:
                issues.append(self._mk_issue(
                    rule_id="G6",
                    severity="error",
                    target_kind="binding",
                    target_id=_get_attr(binding, "binding_id", ""),
                    field_name="domain_id",
                    message=(
                        "binding.domain_id "
                        + repr(domain_id)
                        + " does not refer to any domain "
                        "supplied in the request"
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G7: Attribute.allowed_taxonomy_id must exist
    # -------------------------------------------------------------

    def _rule_g7(
        self,
        request: GraphValidationRequest,
        taxonomies_by_id: dict,
        issues: List[GraphIssue],
    ) -> None:
        for attr in request.attributes:
            tax_id = _get_attr(attr, "allowed_taxonomy_id", None)
            if tax_id is None:
                continue
            if not _is_nonempty_str(tax_id):
                issues.append(self._mk_issue(
                    rule_id="G7",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name="allowed_taxonomy_id",
                    message=(
                        "attribute.allowed_taxonomy_id is not a "
                        "non-empty string"
                    ),
                ))
                continue
            if tax_id not in taxonomies_by_id:
                issues.append(self._mk_issue(
                    rule_id="G7",
                    severity="error",
                    target_kind="attribute",
                    target_id=_get_attr(attr, "attribute_id", ""),
                    field_name="allowed_taxonomy_id",
                    message=(
                        "attribute.allowed_taxonomy_id "
                        + repr(tax_id)
                        + " does not refer to any taxonomy "
                        "supplied in the request"
                    ),
                ))

    # -------------------------------------------------------------
    # Rule G8: Binding.knowledge_object_id must equal request KO id
    # -------------------------------------------------------------

    def _rule_g8(
        self,
        request: GraphValidationRequest,
        issues: List[GraphIssue],
    ) -> None:
        ko_id = _get_attr(
            request.knowledge_object, "knowledge_id", ""
        )
        if not _is_nonempty_str(ko_id):
            return
        for binding in request.bindings:
            b_ko_id = _get_attr(
                binding, "knowledge_object_id", None
            )
            if b_ko_id is None:
                issues.append(self._mk_issue(
                    rule_id="G8",
                    severity="error",
                    target_kind="binding",
                    target_id=_get_attr(binding, "binding_id", ""),
                    field_name="knowledge_object_id",
                    message=(
                        "binding.knowledge_object_id is missing"
                    ),
                ))
                continue
            if b_ko_id != ko_id:
                issues.append(self._mk_issue(
                    rule_id="G8",
                    severity="error",
                    target_kind="binding",
                    target_id=_get_attr(binding, "binding_id", ""),
                    field_name="knowledge_object_id",
                    message=(
                        "binding.knowledge_object_id "
                        + repr(b_ko_id)
                        + " does not match the request's KO id "
                        + repr(ko_id)
                    ),
                ))

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------

    @staticmethod
    def _index_by(
        items: Any,
        id_attr: str,
    ) -> dict:
        out: dict = {}
        if not isinstance(items, (list, tuple)):
            return out
        for item in items:
            if item is None:
                continue
            v = getattr(item, id_attr, None)
            if isinstance(v, str) and v:
                out[v] = item
        return out

    @staticmethod
    def _mk_issue(
        *,
        rule_id: str,
        severity: str,
        target_kind: str,
        target_id: str,
        field_name: Optional[str],
        message: str,
    ) -> GraphIssue:
        return GraphIssue(
            issue_id=_new_id("iss"),
            rule_id=rule_id,
            severity=severity,
            target_kind=target_kind,
            target_id=target_id,
            field_name=field_name,
            message=message,
            created_at=_now(),
        )


def _get_attr(obj: Any, name: str, default: Any) -> Any:
    if obj is None:
        return default
    return getattr(obj, name, default)


__all__ = ["KnowledgeGraphValidator"]
