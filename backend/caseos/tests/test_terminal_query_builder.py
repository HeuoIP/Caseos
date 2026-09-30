"""Tests for the Terminal Query Builder (Sprint 26.0-A).

Coverage:

    * Query text composition: deterministic concat of site fields.
    * Structured constraints: only KnowledgeObject fields, in
      stable order.
    * Semantic concepts: theme / style / preferred_functions
      captured in that order, empty strings skipped.
    * Determinism: identical input -> identical output (modulo
      auto-assigned query_id).
    * Limit clamping.
    * Builder errors when fed a non-TerminalRequest.
    * Builder errors when fed an out-of-range limit.

Architecture boundary (Sprint 26.0-A spec section 7):

    No forbidden imports allowed.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from caseos.terminal import (  # noqa: E402
    DEFAULT_TERMINAL_CONTRACT,
    TerminalQuery,
    TerminalQueryBuilder,
    TerminalQueryBuilderError,
    TerminalRequest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req(**overrides) -> TerminalRequest:
    base = dict(
        site_type="outdoor",
        site_description="kindergarten playground",
        user_requirements="climbing + role_play",
        preferred_theme="forest",
        preferred_style="natural",
        preferred_functions=("climbing", "role_play"),
    )
    base.update(overrides)
    return TerminalRequest(**base)


# ---------------------------------------------------------------------------
# Query text composition
# ---------------------------------------------------------------------------


class TestQueryTextComposition:
    def test_query_text_lowercases_and_joins(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        assert q.query_text == (
            "outdoor kindergarten playground climbing + role_play"
        )

    def test_missing_description_is_skipped(self) -> None:
        req = _req()
        req2 = dataclasses.replace(req, site_description="")
        q = TerminalQueryBuilder().build(req2)
        # site_type + user_requirements only.
        assert "outdoor" in q.query_text
        assert "climbing + role_play" in q.query_text
        assert "  " not in q.query_text  # no double spaces

    def test_only_site_type(self) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="",
            user_requirements="",
            uploaded_asset_ids=("asset-1",),  # T4 satisfaction via assets
        )
        q = TerminalQueryBuilder().build(req)
        assert q.query_text == "outdoor"


# ---------------------------------------------------------------------------
# Structured constraints
# ---------------------------------------------------------------------------


class TestStructuredConstraints:
    def test_constraints_only_emit_when_field_is_set(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        d = q.filters_dict()
        assert d == {
            "site_type": "outdoor",
            "theme": "forest",
            "style": "natural",
        }

    def test_constraints_skip_empty_preferences(self) -> None:
        req = _req(preferred_theme="", preferred_style="")
        q = TerminalQueryBuilder().build(req)
        d = q.filters_dict()
        assert d == {"site_type": "outdoor"}

    def test_constraints_are_tuple_ordered(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        # Insertion order: site_type, theme, style.
        keys = [k for k, _ in q.structured_constraints]
        assert keys == ["site_type", "theme", "style"]


# ---------------------------------------------------------------------------
# Semantic concepts
# ---------------------------------------------------------------------------


class TestSemanticConcepts:
    def test_concepts_capture_preferences_in_order(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        assert q.semantic_concepts == (
            "forest",
            "natural",
            "climbing",
            "role_play",
        )

    def test_concepts_skip_empty_strings(self) -> None:
        req = _req(preferred_functions=("climbing", "", "role_play"))
        q = TerminalQueryBuilder().build(req)
        assert q.semantic_concepts == (
            "forest",
            "natural",
            "climbing",
            "role_play",
        )

    def test_concepts_empty_when_no_preferences(self) -> None:
        req = TerminalRequest(
            site_type="outdoor",
            site_description="x",
            preferred_theme="", preferred_style="",
            preferred_functions=(),
        )
        q = TerminalQueryBuilder().build(req)
        assert q.semantic_concepts == ()


# ---------------------------------------------------------------------------
# Determinism + immutability
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_input_yields_same_query_text(self) -> None:
        req = _req()
        a = TerminalQueryBuilder().build(req)
        b = TerminalQueryBuilder().build(req)
        assert a.query_text == b.query_text
        assert a.structured_constraints == b.structured_constraints
        assert a.semantic_concepts == b.semantic_concepts
        assert a.limit == b.limit
        # query_id is intentionally fresh per call.
        assert a.query_id != b.query_id

    def test_build_returns_frozen_query(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        with pytest.raises(dataclasses.FrozenInstanceError):
            q.limit = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Limit handling
# ---------------------------------------------------------------------------


class TestLimitHandling:
    def test_default_limit(self) -> None:
        q = TerminalQueryBuilder().build(_req())
        assert q.limit == DEFAULT_TERMINAL_CONTRACT.default_limit

    def test_build_with_limit_clamps_low(self) -> None:
        # 0 is invalid -> builder raises; validator is the gate.
        with pytest.raises(TerminalQueryBuilderError):
            TerminalQueryBuilder().build_with_limit(_req(), 0)

    def test_build_with_limit_clamps_high(self) -> None:
        q = TerminalQueryBuilder().build_with_limit(_req(), 10_000)
        assert q.limit == DEFAULT_TERMINAL_CONTRACT.max_limit

    def test_build_with_limit_rejects_negative(self) -> None:
        with pytest.raises(TerminalQueryBuilderError):
            TerminalQueryBuilder().build_with_limit(_req(), -1)

    def test_build_with_limit_rejects_non_int(self) -> None:
        with pytest.raises(TerminalQueryBuilderError):
            TerminalQueryBuilder().build_with_limit(_req(), 3.5)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Builder error handling
# ---------------------------------------------------------------------------


class TestBuilderErrors:
    def test_build_rejects_non_request(self) -> None:
        with pytest.raises(TerminalQueryBuilderError):
            TerminalQueryBuilder().build({"site_type": "x"})  # type: ignore[arg-type]

    def test_construction_rejects_bad_contract(self) -> None:
        with pytest.raises(TerminalQueryBuilderError):
            TerminalQueryBuilder(contract={"default_limit": 1})  # type: ignore[arg-type]
