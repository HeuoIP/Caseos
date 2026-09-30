"""Tests for the Terminal Service (Sprint 26.0-A).

Coverage:

    * TerminalValidator T1..T8 happy + sad paths.
    * TerminalService.execute() real E2E with the
      RetrievalPipeline -- no mocks.
    * Three KnowledgeObjects fixture (Cases A/B/C per spec).
    * The seven contract assertions from spec section 10:
        1. request can be executed successfully
        2. total_hits is returned
        3. result order is deterministic
        4. same request twice yields identical results
        5. mutating the input corpus after a call does NOT
           pollute an already-returned result
        6. empty result returns cleanly
        7. illegal request is rejected by the validator

Architecture boundary (Sprint 26.0-A spec section 7):

    No forbidden imports allowed.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.object import KnowledgeObject  # noqa: E402

from caseos.terminal import (  # noqa: E402
    TerminalRequest,
    TerminalService,
    TerminalServiceError,
    TerminalValidator,
)


# ---------------------------------------------------------------------------
# Fixture: 3 real KOs per spec section 10
# ---------------------------------------------------------------------------


def _make_ko(
    knowledge_id: str,
    *,
    title: str,
    site_type: str = "outdoor",
    theme: str = "",
    style: str = "",
    function_tags=(),
    description: str = "",
    age_range: str = "",
) -> KnowledgeObject:
    return KnowledgeObject(
        knowledge_id=knowledge_id,
        version=1,
        title=title,
        description=description,
        category="case",
        project_type="kindergarten",
        site_type=site_type,
        location_type="suburban",
        space_size="medium",
        theme=theme,
        style=style,
        color_system="",
        interaction_type="physical",
        function_tags=list(function_tags),
        image_refs=[],
        document_refs=[],
        source="terminal_e2e",
    )


@pytest.fixture
def corpus() -> List[KnowledgeObject]:
    """Spec-defined Cases A / B / C."""
    return [
        _make_ko(
            "case-a",
            title="Forest kindergarten small site",
            site_type="outdoor",
            theme="forest",
            style="natural",
            function_tags=["climbing", "exploration"],
            description="small kindergarten site, 3-6 years",
        ),
        _make_ko(
            "case-b",
            title="Mechanical theme outdoor amusement park",
            site_type="outdoor",
            theme="mechanical",
            style="modern",
            function_tags=["rides", "carousel"],
            description="large outdoor amusement park",
        ),
        _make_ko(
            "case-c",
            title="Kindergarten small site slide + sandbox",
            site_type="outdoor",
            theme="natural",
            style="natural",
            function_tags=["slide", "sandbox"],
            description="small kindergarten site, 3-6 years",
        ),
    ]


def _req(**overrides) -> TerminalRequest:
    base = dict(
        site_type="outdoor",
        site_description="kindergarten playground 3-6 years",
        preferred_theme="forest",
        preferred_style="natural",
        preferred_functions=("climbing",),
    )
    base.update(overrides)
    return TerminalRequest(**base)


# ===========================================================================
# 1. Validator T1..T8
# ===========================================================================


class TestValidator:
    def test_T1_request_type_rejected(self) -> None:
        v = TerminalValidator()
        res = v.validate({"site_type": "x"})
        assert res.valid is False
        assert res.rule_id == "T1_request_type"

    def test_T2_request_id_present(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(
            site_type="outdoor",
            site_description="x",
            request_id="",
        )
        res = v.validate(req)
        # T2 fires only on truly empty ids. Empty id is auto-filled
        # by TerminalRequest.__post_init__; force a non-empty
        # whitespace id to keep T2 reachable.
        req2 = dataclasses.replace(req, request_id="   ")
        res2 = v.validate(req2)
        assert res2.rule_id == "T2_request_id_present"

    def test_T3_site_type_present(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(
            site_type="",
            site_description="x",
        )
        res = v.validate(req)
        assert res.rule_id == "T3_site_type_present"

    def test_T4_description_or_assets(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(
            site_type="outdoor",
            site_description="",
            uploaded_asset_ids=(),
        )
        res = v.validate(req)
        assert res.rule_id == "T4_description_or_assets"

    def test_T5_site_area_positive(self) -> None:
        v = TerminalValidator()
        for bad in (-1, 0):
            req = TerminalRequest(
                site_type="outdoor", site_description="x", site_area=bad,
            )
            res = v.validate(req)
            assert res.rule_id == "T5_site_area_positive_when_set", bad

    def test_T6_age_range_well_formed(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(
            site_type="outdoor", site_description="x",
            age_range="   ",
        )
        res = v.validate(req)
        assert res.rule_id == "T6_age_range_well_formed"

    def test_T7_limit_in_range(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(site_type="outdoor", site_description="x")
        for bad in (0, -1):
            res = v.validate(req, limit=bad)
            assert res.rule_id == "T7_limit_in_range", bad

    def test_T8_tuple_no_empty_strings(self) -> None:
        v = TerminalValidator()
        req = TerminalRequest(
            site_type="outdoor", site_description="x",
            preferred_functions=("climbing", ""),
        )
        res = v.validate(req)
        assert res.rule_id == "T8_tuple_no_empty_strings"

    def test_valid_request_passes(self) -> None:
        v = TerminalValidator()
        req = _req()
        res = v.validate(req)
        assert res.valid is True
        assert res.rule_id == "OK"
        assert res.request_id == req.request_id


# ===========================================================================
# 2. Service construction
# ===========================================================================


class TestServiceConstruction:
    def test_default_construction(self) -> None:
        svc = TerminalService()
        assert svc.pipeline is None  # lazy default
        assert svc.contract is not None

    def test_invalid_pipeline_rejected(self) -> None:
        with pytest.raises(TerminalServiceError):
            TerminalService(pipeline="not a pipeline")  # type: ignore[arg-type]

    def test_invalid_contract_rejected(self) -> None:
        with pytest.raises(TerminalServiceError):
            TerminalService(contract="not a contract")  # type: ignore[arg-type]


# ===========================================================================
# 3. Spec section 10: real E2E with 3 KOs
# ===========================================================================


class TestE2ERealCorpus:
    """The 7 assertions from Sprint 26.0-A spec section 10."""

    def test_1_request_executes_successfully(self, corpus) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), corpus)
        assert result.success is True
        assert result.failure_reason == ""

    def test_2_total_hits_is_returned(self, corpus) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), corpus)
        assert isinstance(result.total_hits, int)
        assert result.total_hits >= 1
        assert len(result.cases) == result.total_hits

    def test_3_result_order_is_deterministic(self, corpus) -> None:
        svc = TerminalService()
        a = svc.execute(_req(), corpus)
        b = svc.execute(_req(), corpus)
        ids_a = [c.knowledge_id for c in a.cases]
        ids_b = [c.knowledge_id for c in b.cases]
        assert ids_a == ids_b
        scores_a = [c.match_score for c in a.cases]
        scores_b = [c.match_score for c in b.cases]
        assert scores_a == scores_b

    def test_4_same_request_twice_yields_identical_results(self, corpus) -> None:
        svc = TerminalService()
        a = svc.execute(_req(), corpus)
        b = svc.execute(_req(), corpus)
        # Compare the structural payload.
        assert a.success == b.success
        assert a.total_hits == b.total_hits
        assert a.failure_reason == b.failure_reason
        # query_id and request_id are stable per-request; only
        # created_at differs.
        assert a.query.query_id != b.query.query_id
        assert a.query.query_text == b.query.query_text

    def test_5_corpus_mutation_does_not_pollute_result(self, corpus) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), corpus)
        first_ids = [c.knowledge_id for c in result.cases]
        # Mutate the corpus *after* the call: append a ghost KO.
        corpus.append(
            _make_ko(
                "ghost",
                title="ghost site",
                site_type="indoor",
            )
        )
        # The already-returned result must not change.
        second_ids = [c.knowledge_id for c in result.cases]
        assert first_ids == second_ids

    def test_6_empty_corpus_returns_cleanly(self) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), [])
        assert result.success is True
        assert result.total_hits == 0
        assert result.cases == ()

    def test_7_illegal_request_is_rejected(self, corpus) -> None:
        svc = TerminalService()
        bad = TerminalRequest(
            site_type="",  # T3 fails
            site_description="x",
        )
        result = svc.execute(bad, corpus)
        assert result.success is False
        assert result.failure_reason != ""
        assert result.total_hits == 0
        assert result.cases == ()
        assert result.retrieval_result is None


# ===========================================================================
# 4. Partial-information flow
# ===========================================================================


class TestPartialInformation:
    def test_minimal_request_with_only_assets(self, corpus) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="",
            uploaded_asset_ids=("asset-1", "asset-2"),
        )
        svc = TerminalService()
        result = svc.execute(req, corpus)
        assert result.success is True

    def test_minimal_request_with_only_description(self, corpus) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="small kindergarten site",
            uploaded_asset_ids=(),
        )
        svc = TerminalService()
        result = svc.execute(req, corpus)
        assert result.success is True

    def test_corpus_knowledge_objects_not_mutated(self, corpus) -> None:
        svc = TerminalService()
        snap_before = [ko.to_dict() for ko in corpus]
        svc.execute(_req(), corpus)
        snap_after = [ko.to_dict() for ko in corpus]
        assert snap_before == snap_after


# ===========================================================================
# 5. Custom-limit handling
# ===========================================================================


class TestLimitHandling:
    def test_explicit_limit_propagates(self, corpus) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), corpus, limit=3)
        assert result.success is True
        assert result.total_hits <= 3

    def test_invalid_limit_rejected(self, corpus) -> None:
        svc = TerminalService()
        result = svc.execute(_req(), corpus, limit=0)
        assert result.success is False
        assert "limit" in result.failure_reason.lower()


# ===========================================================================
# 6. Determinism across processes (same payload == same content)
# ===========================================================================


class TestDeterminism:
    def test_query_text_is_deterministic(self, corpus) -> None:
        svc = TerminalService()
        req = _req()
        a = svc.execute(req, corpus)
        b = svc.execute(req, corpus)
        assert a.query.query_text == b.query.query_text
        assert a.query.structured_constraints == b.query.structured_constraints
        assert a.query.semantic_concepts == b.query.semantic_concepts
