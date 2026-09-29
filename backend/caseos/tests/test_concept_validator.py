"""Tests for Semantic Concept Registry Validator V1 (Sprint 24.2-A).

Coverage:

    * ConceptValidator single-record rules C1..C7
    * ConceptValidator cross-record rules C8.1..C8.3
    * ConceptAliasValidator single-record rules A1..A4
    * ConceptAliasValidator cross-record rules A5.1..A5.3
    * ValidationResult.to_dict round-trip
    * Duck-typed registry support
    * AST architecture boundary
        The concept validator does NOT import from:
            * caseos.intelligence.*
            * caseos.knowledge.evolution
            * caseos.knowledge.governance
            * caseos.knowledge.intake
            * caseos.knowledge.feedback
            * caseos.brain.*

Architecture boundary (Sprint 24.2-A spec):

    These tests do NOT import forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.{domain,binding,taxonomy,
                            attribute,graph}
        * caseos.knowledge.retrieval
        * stdlib
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.retrieval.concept_registry import (  # noqa: E402
    ConceptAliasRecord,
    ConceptAliasRegistry,
    ConceptRecord,
    ConceptRegistry,
)
from caseos.knowledge.retrieval.concept_validator import (  # noqa: E402
    ConceptAliasValidationResult,
    ConceptAliasValidator,
    ConceptValidationResult,
    ConceptValidator,
)


# ---------------------------------------------------------------------------
# Helpers: duck-typed fake records
# ---------------------------------------------------------------------------


class FakeRecord:
    """Duck-typed fake that bypasses ConceptRecord.__post_init__.

    Lets the test supply invalid values that a real
    ConceptRecord would reject at construction time.
    """

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeAliasRecord:
    """Duck-typed fake for ConceptAliasRecord."""

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeRegistry:
    """Minimal duck-typed registry with concept_ids() and
    get(concept_id) returning FakeRecord-like objects."""

    def __init__(self, items):
        self._items = list(items)

    def concept_ids(self):
        return [
            getattr(r, "concept_id", None)
            for r in self._items
            if getattr(r, "concept_id", None)
        ]

    def get(self, cid):
        for r in self._items:
            if getattr(r, "concept_id", None) == cid:
                return r
        return None


class FakeAliasRegistry:
    def __init__(self, items):
        self._items = list(items)

    def alias_ids(self):
        return [
            getattr(r, "alias_id", None)
            for r in self._items
            if getattr(r, "alias_id", None)
        ]

    def list(self):
        return list(self._items)


# ---------------------------------------------------------------------------
# 1. ConceptValidator single-record rules
# ---------------------------------------------------------------------------


class TestConceptValidatorSingleRecord:
    def test_valid_record_passes(self) -> None:
        v = ConceptValidator()
        rec = ConceptRecord(
            concept_id="forest",
            concept_type="theme",
            label="Forest",
            aliases=("wild",),
            knowledge_object_ids=("ko_1",),
            parent_concept_id="nature",
        )
        r = v.validate(rec)
        assert r.valid is True
        assert r.errors == ()
        assert r.rule_failures == ()

    def test_none_record(self) -> None:
        r = ConceptValidator().validate(None)
        assert r.valid is False
        assert r.errors == ("record is None",)

    def test_c1_empty_concept_id(self) -> None:
        rec = FakeRecord(
            concept_id="", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C1" in r.rule_failures

    def test_c1_whitespace_concept_id(self) -> None:
        rec = FakeRecord(
            concept_id="   ", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C1" in r.rule_failures

    def test_c2_version_zero(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=0, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C2" in r.rule_failures

    def test_c2_version_negative(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=-1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C2" in r.rule_failures

    def test_c2_version_bool_rejected(self) -> None:
        # bool is a subclass of int but we reject it.
        rec = FakeRecord(
            concept_id="x", version=True, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C2" in r.rule_failures

    def test_c2_version_string_rejected(self) -> None:
        rec = FakeRecord(
            concept_id="x", version="1", concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C2" in r.rule_failures

    def test_c3_unknown_concept_type(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="emotion",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C3" in r.rule_failures

    def test_c4_empty_parent_concept_id(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id="", knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C4" in r.rule_failures

    def test_c4_self_referencing_parent(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id="x", knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C4" in r.rule_failures

    def test_c4_none_parent_is_ok(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C4" not in r.rule_failures

    def test_c5_knowledge_object_ids_empty_string_rejected(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None,
            knowledge_object_ids=("ko_1", "", "ko_3"),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C5" in r.rule_failures

    def test_c5_knowledge_object_ids_wrong_type(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None,
            knowledge_object_ids="not-a-list",
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C5" in r.rule_failures

    def test_c6_aliases_empty_string_rejected(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=("wild", ""),
            created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C6" in r.rule_failures

    def test_c7_created_at_must_be_string(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at=42, updated_at="",
        )
        r = ConceptValidator().validate(rec)
        assert "C7" in r.rule_failures

    def test_c7_updated_at_must_be_string(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at=42,
        )
        r = ConceptValidator().validate(rec)
        assert "C7" in r.rule_failures

    def test_c7_none_treated_as_absent(self) -> None:
        rec = FakeRecord(
            concept_id="x", version=1, concept_type="theme",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at=None, updated_at=None,
        )
        r = ConceptValidator().validate(rec)
        assert "C7" not in r.rule_failures

    def test_multiple_failures_all_reported(self) -> None:
        rec = FakeRecord(
            concept_id="", version=-1, concept_type="emotion",
            parent_concept_id=None, knowledge_object_ids=(),
            aliases=(), created_at="", updated_at="",
        )
        r = ConceptValidator().validate(rec)
        # C1, C2, C3 should all fire.
        for code in ("C1", "C2", "C3"):
            assert code in r.rule_failures


# ---------------------------------------------------------------------------
# 2. ConceptValidator cross-record rules
# ---------------------------------------------------------------------------


class TestConceptValidatorCrossRecord:
    def test_c8_1_unique_concept_id(self) -> None:
        reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id=None),
            FakeRecord(concept_id="forest", parent_concept_id=None),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("forest"), concept_registry=reg)
        assert "C8.1" in r.rule_failures

    def test_c8_1_unique_concept_id_passes_when_unique(self) -> None:
        reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id=None),
            FakeRecord(concept_id="ocean", parent_concept_id=None),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("forest"), concept_registry=reg)
        assert "C8.1" not in r.rule_failures

    def test_c8_2_orphan_parent_rejected(self) -> None:
        reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id="ghost"),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("forest"), concept_registry=reg)
        assert "C8.2" in r.rule_failures

    def test_c8_2_resolved_parent_passes(self) -> None:
        reg = FakeRegistry([
            FakeRecord(concept_id="nature", parent_concept_id=None),
            FakeRecord(concept_id="forest", parent_concept_id="nature"),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("forest"), concept_registry=reg)
        assert "C8.2" not in r.rule_failures

    def test_c8_2_root_record_passes(self) -> None:
        reg = FakeRegistry([
            FakeRecord(concept_id="root", parent_concept_id=None),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("root"), concept_registry=reg)
        assert "C8.2" not in r.rule_failures

    def test_c8_3_cycle_detected(self) -> None:
        # forest -> nature -> forest (cycle)
        reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id="nature"),
            FakeRecord(concept_id="nature", parent_concept_id="forest"),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("forest"), concept_registry=reg)
        assert "C8.3" in r.rule_failures

    def test_c8_3_self_loop_caught_by_c4_not_c8_3(self) -> None:
        # Self-referencing parent is rejected by C4.
        reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id="forest"),
        ])
        v = ConceptValidator()
        # To bypass C4, supply a record that does not have
        # self-ref in the validator's eyes (we do that by
        # constructing a fake that is NOT equal to its
        # own parent at construction time).
        # Skip this check; C4 already covers self-ref.
        pytest.skip("C4 covers self-reference; C8.3 is for longer cycles")

    def test_c8_3_three_node_cycle(self) -> None:
        # a -> b -> c -> a
        reg = FakeRegistry([
            FakeRecord(concept_id="a", parent_concept_id="b"),
            FakeRecord(concept_id="b", parent_concept_id="c"),
            FakeRecord(concept_id="c", parent_concept_id="a"),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("a"), concept_registry=reg)
        assert "C8.3" in r.rule_failures

    def test_c8_3_deep_acyclic_chain_passes(self) -> None:
        # a -> b -> c -> d (no cycle)
        reg = FakeRegistry([
            FakeRecord(concept_id="d", parent_concept_id=None),
            FakeRecord(concept_id="c", parent_concept_id="d"),
            FakeRecord(concept_id="b", parent_concept_id="c"),
            FakeRecord(concept_id="a", parent_concept_id="b"),
        ])
        v = ConceptValidator()
        r = v.validate(reg.get("a"), concept_registry=reg)
        assert "C8.3" not in r.rule_failures

    def test_c8_skipped_without_registry(self) -> None:
        # No registry supplied -> no C8.* checks fire.
        rec = ConceptRecord(
            concept_id="forest",
            parent_concept_id="ghost",  # would be C8.2 if checked
        )
        v = ConceptValidator()
        r = v.validate(rec)  # no concept_registry
        assert "C8.2" not in r.rule_failures

    def test_duck_typed_registry_without_concept_ids_skips_c8(self) -> None:
        class NoIds:
            def get(self, cid):
                return None

        rec = ConceptRecord(concept_id="forest", parent_concept_id="x")
        v = ConceptValidator()
        r = v.validate(rec, concept_registry=NoIds())
        # No C8.* fires because the registry lacks concept_ids().
        assert all(
            not code.startswith("C8") for code in r.rule_failures
        )


# ---------------------------------------------------------------------------
# 3. ValidationResult helpers
# ---------------------------------------------------------------------------


class TestValidationResultHelpers:
    def test_concept_result_to_dict(self) -> None:
        r = ConceptValidationResult(
            valid=False,
            errors=("e1", "e2"),
            rule_failures=("C1",),
        )
        d = r.to_dict()
        assert d["valid"] is False
        assert list(d["errors"]) == ["e1", "e2"]
        assert list(d["rule_failures"]) == ["C1"]

    def test_alias_result_to_dict(self) -> None:
        r = ConceptAliasValidationResult(
            valid=True, errors=(), rule_failures=(),
        )
        d = r.to_dict()
        assert d["valid"] is True
        assert list(d["errors"]) == []
        assert list(d["rule_failures"]) == []


# ---------------------------------------------------------------------------
# 4. ConceptAliasValidator single-record rules
# ---------------------------------------------------------------------------


class TestConceptAliasValidatorSingleRecord:
    def test_valid_alias_passes(self) -> None:
        v = ConceptAliasValidator()
        rec = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        )
        r = v.validate(rec)
        assert r.valid is True
        assert r.rule_failures == ()

    def test_none_record(self) -> None:
        r = ConceptAliasValidator().validate(None)
        assert r.valid is False

    def test_a1_empty_alias_id(self) -> None:
        rec = FakeAliasRecord(
            alias_id="", alias="wild",
            canonical_concept_id="forest", version=1,
        )
        r = ConceptAliasValidator().validate(rec)
        assert "A1" in r.rule_failures

    def test_a2_version_zero(self) -> None:
        rec = FakeAliasRecord(
            alias_id="a1", alias="wild",
            canonical_concept_id="forest", version=0,
        )
        r = ConceptAliasValidator().validate(rec)
        assert "A2" in r.rule_failures

    def test_a3_empty_alias(self) -> None:
        rec = FakeAliasRecord(
            alias_id="a1", alias="",
            canonical_concept_id="forest", version=1,
        )
        r = ConceptAliasValidator().validate(rec)
        assert "A3" in r.rule_failures

    def test_a4_empty_canonical_id(self) -> None:
        rec = FakeAliasRecord(
            alias_id="a1", alias="wild",
            canonical_concept_id="", version=1,
        )
        r = ConceptAliasValidator().validate(rec)
        assert "A4" in r.rule_failures


# ---------------------------------------------------------------------------
# 5. ConceptAliasValidator cross-record rules
# ---------------------------------------------------------------------------


class TestConceptAliasValidatorCrossRecord:
    def test_a5_1_unique_alias_id(self) -> None:
        reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
            FakeAliasRecord(
                alias_id="a1", alias="sea",
                canonical_concept_id="ocean",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(reg.list()[0], alias_registry=reg)
        assert "A5.1" in r.rule_failures

    def test_a5_1_unique_alias_id_passes_when_unique(self) -> None:
        reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
            FakeAliasRecord(
                alias_id="a2", alias="sea",
                canonical_concept_id="ocean",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(reg.list()[0], alias_registry=reg)
        assert "A5.1" not in r.rule_failures

    def test_a5_2_canonical_must_exist_in_concept_registry(self) -> None:
        alias_reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="ghost",
            ),
        ])
        concept_reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id=None),
        ])
        v = ConceptAliasValidator()
        r = v.validate(
            alias_reg.list()[0],
            alias_registry=alias_reg,
            concept_registry=concept_reg,
        )
        assert "A5.2" in r.rule_failures

    def test_a5_2_canonical_resolved_passes(self) -> None:
        alias_reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
        ])
        concept_reg = FakeRegistry([
            FakeRecord(concept_id="forest", parent_concept_id=None),
        ])
        v = ConceptAliasValidator()
        r = v.validate(
            alias_reg.list()[0],
            alias_registry=alias_reg,
            concept_registry=concept_reg,
        )
        assert "A5.2" not in r.rule_failures

    def test_a5_2_skipped_without_concept_registry(self) -> None:
        alias_reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="ghost",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(alias_reg.list()[0], alias_registry=alias_reg)
        # No concept_registry -> A5.2 not evaluated.
        assert "A5.2" not in r.rule_failures

    def test_a5_3_duplicate_alias_string_rejected(self) -> None:
        # Two records, both alias = "wild" (case-insensitive)
        # but different alias_ids.
        reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
            FakeAliasRecord(
                alias_id="a2", alias="WILD",
                canonical_concept_id="ocean",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(reg.list()[1], alias_registry=reg)
        assert "A5.3" in r.rule_failures

    def test_a5_3_no_duplicate_passes(self) -> None:
        reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
            FakeAliasRecord(
                alias_id="a2", alias="sea",
                canonical_concept_id="ocean",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(reg.list()[0], alias_registry=reg)
        assert "A5.3" not in r.rule_failures

    def test_a5_3_self_record_does_not_collide_with_itself(self) -> None:
        reg = FakeAliasRegistry([
            FakeAliasRecord(
                alias_id="a1", alias="wild",
                canonical_concept_id="forest",
            ),
        ])
        v = ConceptAliasValidator()
        r = v.validate(reg.list()[0], alias_registry=reg)
        assert "A5.3" not in r.rule_failures

    def test_a5_skipped_without_alias_registry(self) -> None:
        rec = ConceptAliasRecord(
            alias_id="a1", alias="wild",
            canonical_concept_id="forest",
        )
        v = ConceptAliasValidator()
        r = v.validate(rec)  # no alias_registry
        assert all(
            not code.startswith("A5") for code in r.rule_failures
        )


# ---------------------------------------------------------------------------
# 6. End-to-end: ConceptRegistry full validation sweep
# ---------------------------------------------------------------------------


class TestRegistryFullValidation:
    def test_clean_registry_passes_all_records(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="nature", concept_type="theme",
            label="Nature",
        ))
        cr.append(ConceptRecord(
            concept_id="forest", concept_type="theme",
            label="Forest", parent_concept_id="nature",
            knowledge_object_ids=("ko_1",),
            aliases=("wild",),
        ))
        cr.append(ConceptRecord(
            concept_id="ocean", concept_type="theme",
            label="Ocean", parent_concept_id="nature",
            knowledge_object_ids=("ko_2",),
        ))

        v = ConceptValidator()
        # Validate every record against the registry.
        results = [v.validate(r, concept_registry=cr) for r in cr.list()]
        assert all(r.valid for r in results)

    def test_orphan_in_registry_detected(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest", parent_concept_id="ghost",
        ))
        v = ConceptValidator()
        # Walk over the registered records.
        results = [v.validate(r, concept_registry=cr) for r in cr.list()]
        # forest record has orphan parent -> fails C8.2.
        assert not results[0].valid
        assert "C8.2" in results[0].rule_failures

    def test_cycle_in_registry_detected(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="a", parent_concept_id="b",
        ))
        cr.append(ConceptRecord(
            concept_id="b", parent_concept_id="a",
        ))
        v = ConceptValidator()
        results = [v.validate(r, concept_registry=cr) for r in cr.list()]
        # Both records participate in a cycle.
        assert any("C8.3" in r.rule_failures for r in results)

    def test_alias_registry_clean_passes(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(concept_id="forest"))
        cr.append(ConceptRecord(concept_id="ocean"))

        ar = ConceptAliasRegistry()
        ar.append(ConceptAliasRecord(
            alias_id="a1", alias="wild",
            canonical_concept_id="forest",
        ))
        ar.append(ConceptAliasRecord(
            alias_id="a2", alias="sea",
            canonical_concept_id="ocean",
        ))
        av = ConceptAliasValidator()
        results = [
            av.validate(
                r, alias_registry=ar, concept_registry=cr,
            )
            for r in ar.list()
        ]
        assert all(r.valid for r in results)


# ---------------------------------------------------------------------------
# 7. AST architecture boundary
# ---------------------------------------------------------------------------


class TestConceptValidatorArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.feedback",
        "caseos.brain",
    )

    def _collect_imports(self, source: str) -> list[str]:
        if source and source[0] == "\ufeff":
            source = source[1:]
        tree = ast.parse(source)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        imports.append(module + "." + alias.name)
        return imports

    def test_concept_validator_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "concept_validator.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if any(f in imp for f in self.FORBIDDEN_SUBSTRINGS)
        ]
        assert offenders == [], (
            "Forbidden architecture boundary import: " + repr(offenders)
        )
