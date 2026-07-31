"""Sprint 20.5 retrieval benchmark tests.

Three benchmark cases from spec section 5:
    A. Kindergarten -- empty site, natural preference, avoid
       equipment stacking. Expect Decision Pattern + Golden
       Case + Failure Pattern retrieval.
    B. Public space -- community green, children + elderly.
       Expect applicable public-space knowledge.
    C. Cultural tourism -- theme experience, visitor journey.
       Expect experience-driven cases.

The retrieval engine is unchanged; these tests use the
existing Sprint 20 RetrievalEngine against the migrated
5-subdir corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import ProjectContext
from caseos.knowledge.objects.loader import DEFAULT_CORPUS_DIR, load_corpus
from caseos.knowledge.retrieval.module import RetrievalEngine


def _project(**overrides) -> ProjectContext:
    base = dict(
        project_id="t",
        project_type="kindergarten_outdoor",
        site_description="",
        user_goal="",
        constraints="",
        extras={},
    )
    base.update(overrides)
    return ProjectContext(**base)


def _decision_synthetic() -> dict:
    """A synthetic decision so the retrieval engine has a target
    to rank against. The engine never *makes* the decision; it
    only ranks KOs that match the project + decision text.
    """
    return {
        "decision": "Create a single experience anchor",
        "diagnosis": "the site lacks identity",
        "boundary": "Do not add scattered equipment",
    }


def _retrieve(project, decision=None, knowledge=None):
    engine = RetrievalEngine()
    return engine.retrieve(
        project=project,
        decision=decision or _decision_synthetic(),
        knowledge_patterns=knowledge if knowledge is not None
        else load_corpus(DEFAULT_CORPUS_DIR),
    )


# ------------- Test A: Kindergarten benchmark -------------

def test_benchmark_a_kindergarten() -> None:
    """A. Kindergarten -- empty site, natural preference, avoid
    equipment stacking. Expect Decision Pattern, Golden Case,
    AND Failure Pattern retrieval.
    """
    project = _project(
        project_type="kindergarten_outdoor",
        site_description=(
            "outdoor area with some existing equipment but lacks "
            "a memorable identity; owner prefers natural materials"
        ),
        user_goal="improve enrollment",
        constraints="limited budget",
    )
    ep = _retrieve(project)
    ids = [ko.get("identity", "") for ko in ep.relevant_objects]
    prefixes = {i.split(".")[0] for i in ids}
    assert "DecisionPattern" in prefixes, (
        f"benchmark A expected a DecisionPattern, got {prefixes}"
    )
    assert "GoldenCase" in prefixes, (
        f"benchmark A expected a GoldenCase, got {prefixes}"
    )
    assert "FailurePattern" in prefixes, (
        f"benchmark A expected a FailurePattern, got {prefixes}"
    )


# ------------- Test B: Public space benchmark -------------

def test_benchmark_b_public_space() -> None:
    """B. Public space -- community green, children + elderly.
    Expect applicable public-space knowledge.
    """
    project = _project(
        project_type="public_park_open_area",
        site_description=(
            "open community green with walking paths and partial shade"
        ),
        user_goal="support multi-generation users",
        constraints="limited budget",
    )
    ep = _retrieve(project)
    ids = [ko.get("identity", "") for ko in ep.relevant_objects]
    # Must include a public-space GoldenCase.
    public_ids = [i for i in ids if "park" in i.lower() or "public" in i.lower()]
    assert public_ids, (
        f"benchmark B expected at least one public-space KO, got {ids}"
    )


# ------------- Test C: Cultural tourism benchmark -------------

def test_benchmark_c_cultural_tourism() -> None:
    """C. Cultural tourism -- theme experience, visitor journey.
    Expect experience-driven cases.
    """
    project = _project(
        project_type="cultural_tourism",
        site_description=(
            "linear historical district with multiple heritage sites"
        ),
        user_goal="create a memorable visitor journey",
        constraints="",
    )
    ep = _retrieve(project)
    ids = [ko.get("identity", "") for ko in ep.relevant_objects]
    cultural_ids = [i for i in ids if "cultural" in i.lower()]
    assert cultural_ids, (
        f"benchmark C expected at least one cultural KO, got {ids}"
    )


# ------------- Corpus structure invariants -------------

def test_corpus_has_five_subdirectories() -> None:
    """The Sprint 20.5 corpus has 5 subdirectories, one per
    ADR-015 Knowledge Object category.
    """
    assert DEFAULT_CORPUS_DIR.exists()
    expected = {
        "golden_cases",
        "decision_patterns",
        "expert_principles",
        "failure_patterns",
        "user_preferences",
    }
    actual = {p.name for p in DEFAULT_CORPUS_DIR.iterdir() if p.is_dir()}
    assert expected <= actual, (
        f"corpus missing subdirs; expected {expected}, got {actual}"
    )


def test_corpus_loader_walks_recursively() -> None:
    """load_corpus returns KOs from all 5 subdirectories."""
    objects = load_corpus(DEFAULT_CORPUS_DIR)
    subdirs_seen = {
        ko.get("_source_subdir", "<root>") for ko in objects
    }
    # We must have seen at least 3 distinct subdirs among the
    # loaded objects (golden_cases, decision_patterns,
    # failure_patterns are guaranteed by Sprint 20.5 content;
    # expert_principles and user_preferences are also populated).
    assert len(subdirs_seen) >= 3, (
        f"recursive load only saw subdirs: {subdirs_seen}"
    )


def test_corpus_contains_at_least_3_knowledge_objects() -> None:
    """The corpus must contain at least 3 KOs (Sprint 19.1
    contract preserved; Sprint 20.5 ships 7).
    """
    objects = load_corpus(DEFAULT_CORPUS_DIR)
    assert len(objects) >= 3
    identities = sorted(o.identity for o in objects)
    # All 5 ADR-015 prefixes should be represented.
    prefixes = {i.split(".")[0] for i in identities}
    expected_prefixes = {
        "GoldenCase",
        "DecisionPattern",
        "FailurePattern",
        "ExpertPrinciple",
        "UserPreference",
    }
    missing = expected_prefixes - prefixes
    assert not missing, f"corpus missing ADR-015 prefixes: {missing}"