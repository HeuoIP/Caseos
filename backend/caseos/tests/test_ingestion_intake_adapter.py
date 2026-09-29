"""Tests for the Intake -> Case Knowledge Adapter V1 (Sprint 25.1-A inferred).

Coverage:

    * Round-trip mapping RawCaseObject -> CaseKnowledge.
    * Field-by-field correctness for every mapped attribute.
    * Field preservation semantics: ``created_at`` preserved
      when ``preserve_created_at=True``; cleared otherwise.
    * Case-id normalisation: stale ``CK-`` prefix is stripped
      and re-applied so downstream ids are stable.
    * Batch adapt (``adapt_raw_cases``) preserves order and
      fails fast on the first broken input.
    * Source immutability: the raw record is never mutated
      by ``adapt`` or ``adapt_many``.
    * Error paths: empty id, empty source, invalid raw shape,
      raw input that lacks the duck-typed surface.
    * AST architecture boundary:
        - The four core ingestion modules do NOT import
          ``caseos.knowledge.intake`` (rule preserved).
        - The adapter module DOES import
          ``caseos.knowledge.intake`` (by design).

Architecture boundary (Sprint 25.1-A inferred scope):

    The base ingestion package stays pure-schema. The adapter
    is the only ingestion-side module that may touch intake.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.ingestion import (  # noqa: E402
    SOURCE_KIND_INTAKE,
    CaseKnowledge,
)
from caseos.knowledge.ingestion.adapters import (  # noqa: E402
    DEFAULT_INTAKE_ADAPTER,
    IntakeAdapter,
    IntakeAdapterError,
    RawIntakeRecord,
    adapt_raw_case,
    adapt_raw_cases,
)
from caseos.knowledge.intake.object import (  # noqa: E402
    RawCaseObject,
    new_raw_case,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _raw(**overrides) -> RawCaseObject:
    base = dict(
        source="manual:test",
        title="Forest kindergarten case",
        description="A baseline kindergarten case.",
        files=["assets/forest-1.png", "assets/forest-2.png"],
        notes="operator note",
        candidate_tags=["kindergarten", "outdoor"],
        source_reference="Sprint 25.1-A fixture",
    )
    base.update(overrides)
    return new_raw_case(**base)


def _duck_raw(**overrides) -> object:
    """A minimal duck-typed raw object that is NOT a RawCaseObject."""

    class _Duck:
        pass

    d = _Duck()
    for k, v in overrides.items():
        setattr(d, k, v)
    return d


# ---------------------------------------------------------------------------
# 1. Round-trip mapping
# ---------------------------------------------------------------------------


class TestAdaptSingle:
    def test_basic_mapping(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert isinstance(ck, CaseKnowledge)
        assert ck.source == raw.source
        assert ck.title == raw.title
        assert ck.description == raw.description
        assert ck.source_kind == SOURCE_KIND_INTAKE
        assert ck.origin_reference == raw.source_reference
        assert ck.requires_human_review is True

    def test_case_id_uses_ck_prefix(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert ck.case_id.startswith("CK-")
        # The raw id (UUID hex) must survive inside.
        assert raw.id.replace("-", "") in ck.case_id.replace("-", "")

    def test_files_become_linked_assets(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert list(ck.linked_assets) == list(raw.files)

    def test_candidate_tags_become_tags(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert list(ck.tags) == list(raw.candidate_tags)

    def test_knowledge_id_starts_empty(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        # The KO does not exist yet at intake time.
        assert ck.knowledge_id == ""
        assert ck.knowledge_version == 1

    def test_created_at_preserved_by_default(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert ck.created_at == raw.created_at

    def test_created_by_is_intake(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        assert ck.created_by == "intake"


# ---------------------------------------------------------------------------
# 2. Stale CK- prefix normalisation
# ---------------------------------------------------------------------------


class TestCaseIdNormalisation:
    def test_stale_prefix_is_stripped_and_reapplied(self) -> None:
        raw = new_raw_case(
            source="x", title="t",
            raw_id="CK-deadbeef",
        )
        ck = adapt_raw_case(raw)
        assert ck.case_id == "CK-deadbeef"

    def test_bare_id_gets_prefix(self) -> None:
        raw = new_raw_case(
            source="x", title="t",
            raw_id="abc123",
        )
        ck = adapt_raw_case(raw)
        assert ck.case_id == "CK-abc123"

    def test_double_prefix_passes_through(self) -> None:
        # The adapter only strips one CK- prefix; a doubly-
        # prefixed id survives verbatim. This is intentional:
        # we do not want silent mutation of "CK-CK-foo" into
        # "CK-foo" because the raw side may have its own
        # reason for emitting that shape.
        raw = new_raw_case(
            source="x", title="t",
            raw_id="CK-CK-foo",
        )
        ck = adapt_raw_case(raw)
        assert ck.case_id == "CK-CK-foo"


# ---------------------------------------------------------------------------
# 3. Configuration knobs
# ---------------------------------------------------------------------------


class TestAdapterConfig:
    def test_preserve_created_at_false_generates_fresh_timestamp(self) -> None:
        # When preserve is off, the adapter omits created_at
        # so the CaseKnowledge default factory generates a
        # fresh ISO timestamp at construction time. We
        # therefore assert the resulting timestamp is a
        # well-formed ISO 8601 UTC string ending in "Z".
        raw = _raw()
        adapter = IntakeAdapter(preserve_created_at=False)
        ck = adapter.adapt(raw)
        assert ck.created_at.endswith("Z")
        assert "T" in ck.created_at
        assert len(ck.created_at) == 20  # YYYY-MM-DDTHH:MM:SSZ

    def test_preserve_created_at_true_keeps_raw_timestamp(self) -> None:
        raw = _raw()
        adapter = IntakeAdapter(preserve_created_at=True)
        ck = adapter.adapt(raw)
        assert ck.created_at == raw.created_at
        raw = _raw()
        adapter = IntakeAdapter(created_by="manual:operator1")
        ck = adapter.adapt(raw)
        assert ck.created_by == "manual:operator1"

    def test_require_human_review_false(self) -> None:
        raw = _raw()
        adapter = IntakeAdapter(require_human_review=False)
        ck = adapter.adapt(raw)
        assert ck.requires_human_review is False

    def test_invalid_source_kind_rejected(self) -> None:
        with pytest.raises(IntakeAdapterError):
            IntakeAdapter(source_kind="")

    def test_default_adapter_is_shared_singleton(self) -> None:
        a = adapt_raw_case(_raw())
        b = adapt_raw_case(_raw())
        # Each call produces a distinct id, but the adapter
        # singleton is reusable.
        assert isinstance(a, CaseKnowledge)
        assert isinstance(b, CaseKnowledge)


# ---------------------------------------------------------------------------
# 4. Batch adapt
# ---------------------------------------------------------------------------


class TestAdaptMany:
    def test_batch_preserves_order(self) -> None:
        raws = [_raw() for _ in range(3)]
        results = adapt_raw_cases(raws)
        assert len(results) == 3
        for raw, ck in zip(raws, results):
            assert ck.source == raw.source

    def test_batch_empty_input(self) -> None:
        assert adapt_raw_cases([]) == []

    def test_batch_fails_fast(self) -> None:
        good = _raw()
        bad = _duck_raw(id="", source="x", title="t")
        with pytest.raises(IntakeAdapterError):
            adapt_raw_cases([good, bad])

    def test_batch_accepts_duck_typed_input(self) -> None:
        d1 = _duck_raw(
            id="abc", source="x", title="t1",
            files=["a.png"], candidate_tags=["t1"],
            source_reference="ref1", created_at="2026-01-01T00:00:00Z",
        )
        d2 = _duck_raw(
            id="def", source="y", title="t2",
        )
        out = adapt_raw_cases([d1, d2])
        assert out[0].case_id == "CK-abc"
        assert out[1].case_id == "CK-def"


# ---------------------------------------------------------------------------
# 5. Source immutability
# ---------------------------------------------------------------------------


class TestSourceImmutability:
    def test_adapt_does_not_mutate_raw(self) -> None:
        raw = _raw()
        before = raw.to_dict()
        adapt_raw_case(raw)
        after = raw.to_dict()
        assert before == after

    def test_batch_adapt_does_not_mutate_raws(self) -> None:
        raws = [_raw() for _ in range(3)]
        before = [r.to_dict() for r in raws]
        adapt_raw_cases(raws)
        after = [r.to_dict() for r in raws]
        assert before == after

    def test_caller_files_mutation_does_not_leak(self) -> None:
        raw = _raw()
        ck = adapt_raw_case(raw)
        # Mutate the source list AFTER adapt; the CK must be
        # untouched because the adapter deep-copies collections.
        raw.files.append("evil.png")
        assert "evil.png" not in ck.linked_assets


# ---------------------------------------------------------------------------
# 6. Error paths
# ---------------------------------------------------------------------------


class TestErrors:
    def test_empty_id_rejected(self) -> None:
        bad = _duck_raw(id="", source="x", title="t")
        with pytest.raises(IntakeAdapterError):
            adapt_raw_case(bad)

    def test_empty_source_rejected(self) -> None:
        bad = _duck_raw(id="abc", source="", title="t")
        with pytest.raises(IntakeAdapterError):
            adapt_raw_case(bad)

    def test_completely_unrelated_object_rejected(self) -> None:
        class NotARaw:
            pass
        with pytest.raises(IntakeAdapterError):
            adapt_raw_case(NotARaw())

    def test_string_passthrough_rejected(self) -> None:
        with pytest.raises(IntakeAdapterError):
            adapt_raw_case("not a raw case")


# ---------------------------------------------------------------------------
# 7. RawIntakeRecord
# ---------------------------------------------------------------------------


class TestRawIntakeRecord:
    def test_from_raw_case_basic(self) -> None:
        raw = _raw()
        view = RawIntakeRecord.from_raw_case(raw)
        assert view.id == raw.id
        assert view.source == raw.source
        assert view.title == raw.title
        assert view.description == raw.description
        assert view.files == tuple(raw.files)
        assert view.candidate_tags == tuple(raw.candidate_tags)
        assert view.source_reference == raw.source_reference
        assert view.created_at == raw.created_at
        assert view.notes == raw.notes

    def test_from_raw_case_stringifies(self) -> None:
        raw = _raw()
        view = RawIntakeRecord.from_raw_case(raw)
        # All string fields must be plain str even when the
        # raw side carried something exotic.
        for f in (
            view.id, view.source, view.title, view.description,
            view.source_reference, view.created_at, view.notes,
        ):
            assert isinstance(f, str)
        for f in view.files + view.candidate_tags:
            assert isinstance(f, str)

    def test_record_is_frozen(self) -> None:
        view = RawIntakeRecord(id="a", source="x")
        with pytest.raises(Exception):
            view.id = "b"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 8. AST architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    CORE_INGESTION_FILES = (
        "__init__.py",
        "object.py",
        "contract.py",
        "validator.py",
        "report.py",
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

    @pytest.mark.parametrize("filename", CORE_INGESTION_FILES)
    def test_core_modules_do_not_import_intake(
        self, filename: str,
    ) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / filename
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if "caseos.knowledge.intake" in imp
        ]
        assert offenders == [], (
            "Core ingestion module "
            + filename
            + " must NOT import caseos.knowledge.intake; got "
            + repr(offenders)
        )

    def test_adapter_module_DOES_import_intake(self) -> None:
        """Sanity: the adapter is allowed (and expected) to
        import from intake. If this assertion fails it means
        someone removed the only legal bridge."""
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / "adapters"
            / "intake_adapter.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        assert "caseos.knowledge.intake" in source, (
            "intake_adapter.py is the only allowed bridge to "
            "caseos.knowledge.intake; it must reference it"
        )

    @pytest.mark.parametrize(
        "filename",
        ["adapters/__init__.py", "adapters/intake_adapter.py"],
    )
    def test_adapter_modules_have_no_other_forbidden_imports(
        self, filename: str,
    ) -> None:
        FORBIDDEN = (
            "caseos.intelligence",
            "caseos.knowledge.retrieval",
            "caseos.knowledge.evolution",
            "caseos.knowledge.governance",
            "caseos.brain",
        )
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / filename
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if any(f in imp for f in FORBIDDEN)
        ]
        assert offenders == [], (
            "Forbidden import in " + filename + ": "
            + repr(offenders)
        )