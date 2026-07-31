"""Tests for the Knowledge Object validator (Sprint 20.5).

Acceptance criteria from Sprint 20.5 spec section 2:
    * Every Knowledge Object must contain ADR-015 9 fields.
    * Boundary and Applicability are MANDATORY.
    * Objects without Boundary or Applicability must fail validation.

The validator is pure-Python and stdlib-only; these tests
construct minimal in-memory KOs and assert the verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.corpus_migration.validator import (
    REQUIRED_FIELDS,
    MANDATORY_FIELDS,
    validate_knowledge_object,
    validate_corpus,
)


def _valid_ko(**overrides) -> dict:
    """Build a minimal valid KO; fields can be overridden / removed."""
    base = {
        "identity": "GoldenCase.sample_v1",
        "situation_context": {"project_type": "kindergarten_outdoor"},
        "observation": ["children pass through without lingering"],
        "diagnosis": "no emotional anchor",
        "decision": {"strategy": "build a single thematically anchored experience"},
        "principle": "create one memorable experience node before adding facilities",
        "applicability": {"suitable": ["kindergarten_outdoor"]},
        "boundary": ["do not apply when budget cannot support a meaningful anchor"],
        "feedback": [{"outcome": "stay_time_increased", "score": "positive"}],
    }
    base.update(overrides)
    return base


# ------------- Test 1: well-formed KO passes -------------

def test_valid_knowledge_object_passes() -> None:
    result = validate_knowledge_object(_valid_ko())
    assert result.valid is True
    assert result.missing == []
    assert result.errors == []


# ------------- Test 2: top-level non-dict fails -------------

def test_non_dict_top_level_fails() -> None:
    result = validate_knowledge_object(["not", "a", "dict"])
    assert result.valid is False
    assert result.missing == list(REQUIRED_FIELDS)
    assert any("top-level" in e for e in result.errors)


# ------------- Test 3: missing field -------------

def test_missing_field_is_reported() -> None:
    ko = _valid_ko()
    del ko["principle"]
    result = validate_knowledge_object(ko)
    assert result.valid is False
    assert "principle" in result.missing
    assert "principle" not in result.errors  # only mandatory fields get errors


# ------------- Test 4: missing Boundary fails with explicit error -------------

def test_missing_boundary_fails_validation() -> None:
    ko = _valid_ko()
    del ko["boundary"]
    result = validate_knowledge_object(ko)
    assert result.valid is False
    assert "boundary" in result.missing
    assert any("mandatory" in e and "boundary" in e for e in result.errors)


# ------------- Test 5: missing Applicability fails with explicit error -------------

def test_missing_applicability_fails_validation() -> None:
    ko = _valid_ko()
    del ko["applicability"]
    result = validate_knowledge_object(ko)
    assert result.valid is False
    assert "applicability" in result.missing
    assert any("mandatory" in e and "applicability" in e for e in result.errors)


# ------------- Test 6: empty Boundary fails -------------

def test_empty_boundary_fails_validation() -> None:
    ko = _valid_ko(boundary=[])
    result = validate_knowledge_object(ko)
    assert result.valid is False
    assert "boundary" not in result.missing  # present, but empty
    assert any("boundary" in e for e in result.errors)


# ------------- Test 7: empty Applicability fails -------------

def test_empty_applicability_fails_validation() -> None:
    ko = _valid_ko(applicability={})
    result = validate_knowledge_object(ko)
    assert result.valid is False
    assert "applicability" not in result.missing
    assert any("applicability" in e for e in result.errors)


# ------------- Test 8: Applicability with suitable_when also passes -------------

def test_applicability_with_suitable_when_is_accepted() -> None:
    ko = _valid_ko(applicability={
        "suitable_when": ["site is open or under-defined"],
    })
    result = validate_knowledge_object(ko)
    assert result.valid is True


# ------------- Test 9: validate_corpus walks the real corpus -------------

def test_validate_corpus_passes_for_real_corpus() -> None:
    from caseos.knowledge.objects.loader import DEFAULT_CORPUS_DIR
    results = validate_corpus(DEFAULT_CORPUS_DIR)
    # The real corpus has 8 KOs after Sprint 20.5 (3 migrated + 5 new).
    assert len(results) == 8, \
        f"expected 8 KOs in corpus, got {len(results)}"
    for r in results:
        assert r.valid is True, f"KO failed validation: {r}"


# ------------- Test 10: mandatory fields are exactly boundary + applicability -------------

def test_mandatory_fields_are_exactly_boundary_and_applicability() -> None:
    assert MANDATORY_FIELDS == frozenset({"applicability", "boundary"})


# ------------- Test 11: empty string field is treated as missing -------------

def test_empty_string_field_treated_as_missing() -> None:
    ko = _valid_ko(diagnosis="")
    result = validate_knowledge_object(ko)
    assert "diagnosis" in result.missing


# ------------- Test 12: feedback empty list is OK (recommended not mandatory) -------------

def test_empty_feedback_is_acceptable() -> None:
    ko = _valid_ko(feedback=[])
    result = validate_knowledge_object(ko)
    # feedback is required-but-non-mandatory in our spec; an
    # empty list means "no recorded feedback" and is allowed.
    assert result.valid is True