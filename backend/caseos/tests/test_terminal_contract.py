"""Tests for the Terminal MVP V1 contract (Sprint 26.0-A).

Coverage:

    * TerminalRequest: frozen dataclass, tuple-typed collections,
      field auto-fill (request_id, created_at), JSON round-trip.
    * TerminalQuery: structured_constraints view, filters_dict()
      helper, frozen + tuple fields.
    * TerminalResult: cases/cases tuple, JSON round-trip.
    * TerminalValidationResult: shape, JSON round-trip.
    * TerminalContract: rule labels, limit clamping, describe().
    * AST architecture boundary:
        - Terminal must NOT import intelligence / brain / governance /
          feedback / intake / corpus / evolution.

Architecture boundary (Sprint 26.0-A spec section 7):

    This test file may import from:
        * caseos.terminal (the package under test)
        * caseos.knowledge.object (the KO schema, read-only)
        * stdlib / pytest
    This test file MUST NOT import from:
        * caseos.intelligence.*
        * caseos.brain.*
        * caseos.knowledge.evolution.*
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.knowledge.intake
        * caseos.knowledge.corpus
"""
from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.terminal import (  # noqa: E402
    DEFAULT_LIMIT,
    DEFAULT_TERMINAL_CONTRACT,
    MAX_LIMIT,
    MIN_LIMIT,
    RULE_LABELS,
    TerminalContract,
    TerminalQuery,
    TerminalRequest,
    TerminalResult,
    TerminalValidationResult,
)
from caseos.terminal.contract import default_contract  # noqa: E402
from caseos.terminal.object import (  # noqa: E402
    _new_query_id,
    _new_request_id,
)


# ---------------------------------------------------------------------------
# TerminalRequest
# ---------------------------------------------------------------------------


class TestTerminalRequest:
    def test_minimal_request_is_constructible(self) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="small playground",
        )
        assert req.site_type == "outdoor"
        assert req.request_id.startswith("TR-")
        assert req.created_at  # ISO timestamp auto-filled
        assert req.uploaded_asset_ids == ()
        assert req.preferred_functions == ()
        assert req.site_area is None

    def test_request_id_autofilled(self) -> None:
        a = TerminalRequest(site_type="x", site_description="y")
        b = TerminalRequest(site_type="x", site_description="y")
        assert a.request_id.startswith("TR-")
        assert b.request_id.startswith("TR-")
        assert a.request_id != b.request_id

    def test_collection_fields_are_tuples(self) -> None:
        req = TerminalRequest(
            site_type="x",
            site_description="y",
            preferred_functions=["climbing", "role_play"],
            uploaded_asset_ids=["asset-1", "asset-2"],
        )
        assert isinstance(req.preferred_functions, tuple)
        assert isinstance(req.uploaded_asset_ids, tuple)
        assert req.preferred_functions == ("climbing", "role_play")
        assert req.uploaded_asset_ids == ("asset-1", "asset-2")

    def test_mutation_is_blocked(self) -> None:
        req = TerminalRequest(site_type="x", site_description="y")
        with pytest.raises(dataclasses.FrozenInstanceError):
            req.site_type = "mutated"  # type: ignore[misc]

    def test_to_dict_round_trip(self) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="kindergarten playground",
            site_area=120.0,
            preferred_functions=("climbing", "role_play"),
            preferred_theme="forest",
            uploaded_asset_ids=("asset-1",),
            locale="zh-CN",
        )
        d = req.to_dict()
        # JSON-safe round trip.
        s = json.dumps(d)
        d2 = json.loads(s)
        req2 = TerminalRequest.from_dict(d2)
        assert req2.site_type == req.site_type
        assert req2.site_description == req.site_description
        assert req2.site_area == req.site_area
        assert req2.preferred_functions == req.preferred_functions
        assert req2.preferred_theme == req.preferred_theme
        assert req2.uploaded_asset_ids == req.uploaded_asset_ids
        assert req2.locale == req.locale

    def test_request_id_factory_helper(self) -> None:
        rid = _new_request_id()
        assert rid.startswith("TR-")
        assert len(rid) > 5


# ---------------------------------------------------------------------------
# TerminalQuery
# ---------------------------------------------------------------------------


class TestTerminalQuery:
    def test_filters_dict_round_trip(self) -> None:
        q = TerminalQuery(
            query_text="outdoor kindergarten",
            structured_constraints={
                "site_type": "outdoor",
                "theme": "forest",
            },
            semantic_concepts=("forest", "natural"),
            limit=3,
        )
        d = q.filters_dict()
        assert d == {"site_type": "outdoor", "theme": "forest"}

    def test_structured_constraints_are_tuple(self) -> None:
        q = TerminalQuery(
            structured_constraints={"site_type": "outdoor"},
        )
        assert isinstance(q.structured_constraints, tuple)
        # Stable order: insertion order preserved.
        assert q.structured_constraints == (("site_type", "outdoor"),)

    def test_query_id_autofill(self) -> None:
        q = TerminalQuery(query_text="x")
        assert q.query_id.startswith("TQ-")
        assert _new_query_id().startswith("TQ-")

    def test_mutation_is_blocked(self) -> None:
        q = TerminalQuery(query_text="x")
        with pytest.raises(dataclasses.FrozenInstanceError):
            q.limit = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TerminalResult / TerminalValidationResult
# ---------------------------------------------------------------------------


class TestTerminalResult:
    def test_defaults(self) -> None:
        r = TerminalResult()
        assert r.request_id == ""
        assert r.total_hits == 0
        assert r.cases == ()
        assert r.success is False
        assert r.failure_reason == ""

    def test_to_dict_round_trip_no_crash(self) -> None:
        r = TerminalResult(
            request_id="TR-1",
            total_hits=2,
            success=True,
        )
        d = r.to_dict()
        assert d["request_id"] == "TR-1"
        assert d["total_hits"] == 2
        assert d["success"] is True


class TestTerminalValidationResult:
    def test_defaults(self) -> None:
        v = TerminalValidationResult()
        assert v.valid is False
        assert v.rule_id == ""
        assert v.reason == ""
        assert v.request_id == ""

    def test_to_dict(self) -> None:
        v = TerminalValidationResult(
            valid=True, rule_id="OK", reason="ok", request_id="TR-1",
        )
        d = v.to_dict()
        assert d["valid"] is True
        assert d["rule_id"] == "OK"
        assert d["request_id"] == "TR-1"


# ---------------------------------------------------------------------------
# TerminalContract
# ---------------------------------------------------------------------------


class TestTerminalContract:
    def test_default_contract(self) -> None:
        c = default_contract()
        assert c.default_limit == DEFAULT_LIMIT
        assert c.min_limit == MIN_LIMIT
        assert c.max_limit == MAX_LIMIT

    def test_limit_in_range(self) -> None:
        c = TerminalContract(default_limit=5, min_limit=1, max_limit=20)
        assert c.limit_in_range(5) is True
        assert c.limit_in_range(0) is False
        assert c.limit_in_range(21) is False

    def test_clamp_limit(self) -> None:
        c = TerminalContract(default_limit=5, min_limit=1, max_limit=20)
        assert c.clamp_limit(-3) == 1
        assert c.clamp_limit(100) == 20
        assert c.clamp_limit(7) == 7

    def test_summary_matches_rule_labels(self) -> None:
        c = default_contract()
        assert c.summary() == RULE_LABELS

    def test_describe(self) -> None:
        c = default_contract()
        d = c.describe()
        assert "rules" in d
        assert "T1_request_type" in d["rules"]
        assert "T8_tuple_no_empty_strings" in d["rules"]

    def test_invalid_contract_rejected(self) -> None:
        with pytest.raises(ValueError):
            TerminalContract(default_limit=0, min_limit=1, max_limit=5)
        with pytest.raises(ValueError):
            TerminalContract(default_limit=10, min_limit=1, max_limit=5)


# ---------------------------------------------------------------------------
# Architecture boundary AST scan
# ---------------------------------------------------------------------------


FORBIDDEN_SUBSTRINGS = (
    "caseos.intelligence",
    "caseos.brain",
    "caseos.knowledge.evolution",
    "caseos.knowledge.governance",
    "caseos.knowledge.feedback",
    "caseos.knowledge.intake",
    "caseos.knowledge.corpus",
)


class TestArchitectureBoundary:
    def test_terminal_does_not_import_forbidden_modules(self) -> None:
        terminal_root = (
            Path(__file__).resolve().parents[2] / "backend" / "caseos" / "terminal"
        )
        offenders: list = []
        for path in terminal_root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name
                        if any(target.startswith(s) for s in FORBIDDEN_SUBSTRINGS):
                            offenders.append((str(path), target, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if any(mod.startswith(s) for s in FORBIDDEN_SUBSTRINGS):
                        offenders.append((str(path), mod, node.lineno))
        assert offenders == [], "forbidden terminal imports: " + repr(offenders)

    def test_terminal_only_uses_allowed_dependencies(self) -> None:
        # Sanity check that the legitimate deps are reachable.
        from caseos.knowledge.object import KnowledgeObject
        from caseos.knowledge.retrieval.object import RetrievalQuery
        from caseos.knowledge.retrieval.pipeline import (
            RetrievalPipeline, build_default_pipeline,
        )
        assert KnowledgeObject is not None
        assert RetrievalQuery is not None
        assert RetrievalPipeline is not None
        assert build_default_pipeline() is not None
