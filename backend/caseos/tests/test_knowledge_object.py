"""Knowledge Object schema foundation tests (Sprint 23.0-A).

Test scope:

    * KnowledgeObject field completeness, frozenness, JSON
      round-trip
    * KnowledgeObjectValidator (valid + invalid cases)
    * KnowledgeObject version policy (>= 1)
    * KnowledgeObjectSnapshot deep-copy isolation
    * KnowledgeObjectSchema report
    * Architecture boundary (AST scan)

Out of scope:

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
from datetime import datetime, timezone

import pytest

from caseos.knowledge.object import (
    ASSET_FIELDS,
    CASE_CONTEXT_FIELDS,
    CONTENT_FIELDS,
    DESIGN_ATTRIBUTE_FIELDS,
    FIELD_TYPES,
    IDENTITY_FIELDS,
    KnowledgeObject,
    KnowledgeObjectError,
    KnowledgeObjectSchemaError,
    KnowledgeObjectSnapshot,
    KnowledgeObjectValidator,
    METADATA_FIELDS,
    REQUIRED_FIELDS,
    ValidationResult,
    VERSION_POLICY,
    generate_schema_report,
)


KO_ID = "ko-1"
NOW_ISO = "2026-08-04T00:00:00Z"


def _make_knowledge_object(**overrides) -> KnowledgeObject:
    """Return a fully-populated V1 KnowledgeObject."""
    base = dict(
        knowledge_id=KO_ID,
        version=1,
        title="Forest kindergarten",
        description="A nature-based preschool design",
        category="education",
        project_type="kindergarten",
        site_type="suburban",
        location_type="outdoor",
        space_size="500sqm",
        theme="forest",
        style="scandinavian",
        color_system="earth-tones",
        interaction_type="exploratory",
        function_tags=["nature", "play"],
        image_refs=["img/forest-1.jpg"],
        document_refs=["docs/brief.pdf"],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        source="operator",
    )
    base.update(overrides)
    return KnowledgeObject(**base)


@pytest.fixture
def ko() -> KnowledgeObject:
    return _make_knowledge_object()


@pytest.fixture
def validator() -> KnowledgeObjectValidator:
    return KnowledgeObjectValidator()


# ---------------------------------------------------------------------
# Test 1 -- Field completeness
# ---------------------------------------------------------------------


class TestFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(KnowledgeObject)}
        missing = REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on KnowledgeObject: "
            + str(missing)
        )

    def test_field_count_at_least_fifteen(self) -> None:
        assert len(dataclasses.fields(KnowledgeObject)) >= 15, (
            "KnowledgeObject must declare at least 15 fields; got "
            + str(len(dataclasses.fields(KnowledgeObject)))
        )

    def test_required_fields_set_size(self) -> None:
        assert len(REQUIRED_FIELDS) >= 15

    def test_identity_fields(self) -> None:
        for fname in IDENTITY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_content_fields(self) -> None:
        for fname in CONTENT_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_case_context_fields(self) -> None:
        for fname in CASE_CONTEXT_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_design_attribute_fields(self) -> None:
        for fname in DESIGN_ATTRIBUTE_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_asset_fields(self) -> None:
        for fname in ASSET_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_metadata_fields(self) -> None:
        for fname in METADATA_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_field_types_declared(self) -> None:
        for fname in REQUIRED_FIELDS:
            assert fname in FIELD_TYPES, (
                "FIELD_TYPES missing: " + fname
            )


# ---------------------------------------------------------------------
# Test 2 -- Frozen
# ---------------------------------------------------------------------


class TestFrozen:

    def test_dataclass_is_frozen(self, ko) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            ko.title = "changed"  # type: ignore[misc]

    def test_mutation_of_knowledge_id_raises(self, ko) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            ko.knowledge_id = "x"  # type: ignore[misc]

    def test_mutation_of_version_raises(self, ko) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            ko.version = 99  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 3 -- JSON Serialization (round-trip)
# ---------------------------------------------------------------------


class TestJSONSerialization:

    def test_to_dict_returns_dict(self, ko) -> None:
        d = ko.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_contains_all_required_fields(self, ko) -> None:
        d = ko.to_dict()
        for fname in REQUIRED_FIELDS:
            assert fname in d, "missing key in to_dict: " + fname

    def test_from_dict_round_trip(self, ko) -> None:
        d = ko.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        ko2 = KnowledgeObject.from_dict(decoded)
        assert ko2 == ko

    def test_from_dict_missing_optional_uses_default(self) -> None:
        minimal = {
            "knowledge_id": "ko-2",
            "version": 1,
            "title": "x", "description": "x", "category": "x",
            "project_type": "x", "site_type": "x",
            "location_type": "x", "space_size": "x",
            "theme": "x", "style": "x", "color_system": "x",
            "interaction_type": "x",
            "function_tags": ["a"],
            "image_refs": [],
            "document_refs": [],
            "created_at": NOW_ISO, "updated_at": NOW_ISO,
            "source": "",
        }
        ko = KnowledgeObject.from_dict(minimal)
        assert ko.knowledge_id == "ko-2"
        assert ko.function_tags == ["a"]

    def test_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(KnowledgeObjectSchemaError):
            KnowledgeObject.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Test 4 -- Validator
# ---------------------------------------------------------------------


class TestValidator:

    def test_valid_object_passes(self, validator, ko) -> None:
        result = validator.validate(ko)
        assert result.valid is True
        assert result.errors == ()

    def test_validation_result_is_frozen(self, validator, ko) -> None:
        result = validator.validate(ko)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.valid = False  # type: ignore[misc]

    def test_missing_knowledge_id_rejected(self, validator) -> None:
        class Fake:
            version = 1
            title = "x"; description = "x"; category = "x"
            project_type = "x"; site_type = "x"
            location_type = "x"; space_size = "x"
            theme = "x"; style = "x"; color_system = "x"
            interaction_type = "x"
            function_tags = []
            image_refs = []; document_refs = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("knowledge_id" in e for e in result.errors)

    def test_empty_knowledge_id_rejected(self, validator) -> None:
        class Fake:
            knowledge_id = ""
            version = 1
            title = "x"; description = "x"; category = "x"
            project_type = "x"; site_type = "x"
            location_type = "x"; space_size = "x"
            theme = "x"; style = "x"; color_system = "x"
            interaction_type = "x"
            function_tags = []
            image_refs = []; document_refs = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("knowledge_id" in e for e in result.errors)

    def test_invalid_version_type_rejected(self, validator) -> None:
        class Fake:
            knowledge_id = "k1"
            version = "1"
            title = "x"; description = "x"; category = "x"
            project_type = "x"; site_type = "x"
            location_type = "x"; space_size = "x"
            theme = "x"; style = "x"; color_system = "x"
            interaction_type = "x"
            function_tags = []
            image_refs = []; document_refs = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("version" in e for e in result.errors)

    def test_wrong_field_type_rejected(self, validator) -> None:
        class Fake:
            knowledge_id = "k1"
            version = 1
            title = 123  # wrong type
            description = "x"; category = "x"
            project_type = "x"; site_type = "x"
            location_type = "x"; space_size = "x"
            theme = "x"; style = "x"; color_system = "x"
            interaction_type = "x"
            function_tags = []
            image_refs = []; document_refs = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("title" in e for e in result.errors)

    def test_none_object_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False


# ---------------------------------------------------------------------
# Test 5 -- Version policy
# ---------------------------------------------------------------------


class TestVersionPolicy:

    def test_version_one_is_accepted(self) -> None:
        ko = _make_knowledge_object(version=1)
        assert ko.version == 1

    def test_version_zero_rejected(self) -> None:
        with pytest.raises(KnowledgeObjectSchemaError):
            _make_knowledge_object(version=0)

    def test_version_negative_rejected(self) -> None:
        with pytest.raises(KnowledgeObjectSchemaError):
            _make_knowledge_object(version=-1)

    def test_version_policy_first_is_one(self) -> None:
        assert VERSION_POLICY["first_version"] == 1
        assert VERSION_POLICY["min_version"] == 1

    def test_higher_versions_accepted(self) -> None:
        ko = _make_knowledge_object(version=42)
        assert ko.version == 42


# ---------------------------------------------------------------------
# Test 6 -- Snapshot isolation
# ---------------------------------------------------------------------


class TestSnapshotIsolation:

    def test_snapshot_from_knowledge_object(self, ko) -> None:
        snap = KnowledgeObjectSnapshot.from_knowledge_object(ko)
        assert snap.knowledge_id == ko.knowledge_id
        assert snap.version == ko.version
        assert snap.snapshot == ko.to_dict()
        assert snap.source_object_id == ko.knowledge_id

    def test_snapshot_is_frozen(self, ko) -> None:
        snap = KnowledgeObjectSnapshot.from_knowledge_object(ko)
        with pytest.raises(dataclasses.FrozenInstanceError):
            snap.version = 99  # type: ignore[misc]

    def test_snapshot_deep_copy(self, ko) -> None:
        snap = KnowledgeObjectSnapshot.from_knowledge_object(ko)
        # Mutate the original function_tags list.
        ko.function_tags.append("INJECTED")  # type: ignore[attr-defined]
        # Snapshot must not have seen the new tag.
        assert "INJECTED" not in snap.snapshot["function_tags"]

    def test_snapshot_dict_mutation_isolation(self, ko) -> None:
        snap = KnowledgeObjectSnapshot.from_knowledge_object(ko)
        snap.snapshot["INJECTED"] = True
        # Original object should not see the injection.
        d2 = ko.to_dict()
        assert "INJECTED" not in d2

    def test_snapshot_to_dict_json_safe(self, ko) -> None:
        snap = KnowledgeObjectSnapshot.from_knowledge_object(ko)
        encoded = json.dumps(snap.to_dict())
        decoded = json.loads(encoded)
        assert decoded["knowledge_id"] == ko.knowledge_id
        assert decoded["version"] == ko.version


# ---------------------------------------------------------------------
# Test 7 -- Architecture Boundary (AST)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    FORBIDDEN_PREFIXES = (
        "caseos.intelligence.decision",
        "caseos.intelligence.trust",
        "caseos.intelligence.recommendation",
        "caseos.knowledge.retrieval",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
    )

    def _imported_modules(self, path: pathlib.Path):
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    names.append(module + "." + alias.name)
        return names

    @pytest.mark.parametrize("relative_path", [
        "__init__.py",
        "object.py",
        "schema.py",
        "validator.py",
        "snapshot.py",
        "report.py",
    ])
    def test_knowledge_object_no_forbidden_imports(
        self, relative_path,
    ) -> None:
        pkg_root = (
            pathlib.Path(__file__).resolve().parent.parent.joinpath(
                "knowledge", "object",
            )
        )
        py_file = pkg_root / relative_path
        if not py_file.exists():
            pytest.skip("file not present: " + str(py_file))
        imported = self._imported_modules(py_file)
        for mod in imported:
            for forbidden in self.FORBIDDEN_PREFIXES:
                assert not mod.startswith(forbidden), (
                    py_file.name + " imports forbidden module: "
                    + mod + " (prefix: " + forbidden + ")"
                )


# ---------------------------------------------------------------------
# Bonus -- Schema report
# ---------------------------------------------------------------------


class TestSchemaReport:

    def test_report_contains_required_sections(self) -> None:
        report = generate_schema_report()
        for required in (
            "# Knowledge Object Schema Report",
            "## Identity",
            "## Context",
            "## Design Attributes",
            "## Assets",
            "## Version Policy",
            "## Validation Rules",
        ):
            assert required in report, (
                "missing section: " + required
            )

    def test_report_lists_required_field_count(self) -> None:
        report = generate_schema_report()
        assert (
            "Total required fields: " + str(len(REQUIRED_FIELDS))
            in report
        )
