"""Admission -> Terminal E2E Integration V1 (Sprint 26.1-A).

This test wires Sprint 25.4-A's ``AdmissionWriter.write()``
into Sprint 26.0-A's ``TerminalService.execute()`` and
verifies the V1 chain end-to-end:

    RawCaseObject (Intake)
        |
        v
    IntakeAdapter.adapt()
        |
        v
    CaseKnowledge
        |
        v
    PromotionEligibilityChecker
        |
        v
    PromotionCandidate (ELIGIBLE)
        |
        v
    AdmissionChecker
        |
        v
    AdmissionCandidate (ADMISSIBLE)
        |
        v
    AdmissionWriter.write()
        |
        v
    KnowledgeObject v1  +  KnowledgeVersion  +  AuditRecord
        |
        v
    TerminalService.execute(request, knowledge_objects)
        |
        v
    TerminalResult.total_hits >= 1

Scope discipline (Sprint 26.1-A spec)
-------------------------------------

* No production glue module is added. The test file
  reuses ``_run_e2e_happy`` from
  ``test_ingestion_lifecycle_e2e`` (Sprint 25.4-B) plus
  one test-only helper for multi-corpus cases with custom
  proposal overrides.
* No existing production module is modified.
* The 25.4-B happy path stays untouched; the legacy
  ``IntakeManager.promote()`` path is NOT exercised.

Architecture boundary (this test file)
--------------------------------------

    This file may import from:
        * caseos.knowledge.intake.object          (RawCaseObject)
        * caseos.knowledge.ingestion              (CaseKnowledge / IngestionValidator)
        * caseos.knowledge.ingestion.adapters     (IntakeAdapter)
        * caseos.knowledge.ingestion.promotion    (PromotionCandidate + Checker)
        * caseos.knowledge.ingestion.admission    (AdmissionCandidate + Checker + Writer)
        * caseos.knowledge.evolution.audit        (EvolutionAuditStore)
        * caseos.knowledge.evolution.versioning   (VersionStore)
        * caseos.knowledge.object                 (KnowledgeObject)
        * caseos.knowledge.retrieval.pipeline     (RetrievalPipeline, indirect)
        * caseos.terminal                         (TerminalRequest + TerminalService)
        * tests.test_ingestion_lifecycle_e2e      (test-only glue, 25.4-B)
        * stdlib / pytest

    This file MUST NOT import from:
        * caseos.intelligence.*
        * caseos.brain.*
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.knowledge.corpus
        * caseos.knowledge.evolution (except .audit and .versioning)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Tuple

import pytest

# Match the existing pattern from 25.4-B.
#   - parents[2] = backend/        -> caseos.X.Y import works
# We deliberately do NOT add backend/caseos/ to sys.path: that
# would shadow the top-level backend/tests/ package for the
# rest of the pytest run. Cross-file test glue is loaded
# via importlib below.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.evolution.audit import EvolutionAuditStore  # noqa: E402
from caseos.knowledge.evolution.versioning import VersionStore  # noqa: E402
from caseos.knowledge.ingestion.admission import (  # noqa: E402
    CREATED,
    IDEMPOTENT,
    NOT_ADMISSIBLE,
    REJECTED,
    AdmissionCandidate,
    AdmissionChecker,
    AdmissionWriter,
    DuplicateAdmissionError,
    new_admission_candidate,
)
from caseos.knowledge.ingestion.promotion import (  # noqa: E402
    PromotionEligibilityChecker,
)
from caseos.knowledge.object import KnowledgeObject  # noqa: E402
from caseos.terminal import TerminalRequest, TerminalService  # noqa: E402

# Reuse 25.4-B test-only glue (no production module added).
# Loaded via importlib to avoid polluting sys.path and
# shadowing the top-level backend/tests/ package.
import importlib.util as _importlib_util  # noqa: E402

_HELPER_PATH = Path(__file__).resolve().parent / "test_ingestion_lifecycle_e2e.py"
_spec = _importlib_util.spec_from_file_location(
    "_e2e_helpers_25_4_b", _HELPER_PATH,
)
if _spec is None or _spec.loader is None:
    raise ImportError("cannot load 25.4-B test helper: " + str(_HELPER_PATH))
_helpers = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)

_build_admission_candidate = _helpers._build_admission_candidate
_build_admission_proposal = _helpers._build_admission_proposal
_build_case_knowledge = _helpers._build_case_knowledge
_build_provenance_chain = _helpers._build_provenance_chain
_build_promotion_candidate = _helpers._build_promotion_candidate
_build_raw_case = _helpers._build_raw_case
_run_e2e_happy = _helpers._run_e2e_happy


# ---------------------------------------------------------------------------
# Test-only fixture helpers
# ---------------------------------------------------------------------------

FOREST_KO_ID: str = "ko_forest_v1"
OCEAN_KO_ID: str = "ko_ocean_v1"
URBAN_KO_ID: str = "ko_urban_v1"


def _build_one_admission_with_overrides(
    target_id: str,
    *,
    theme: str,
    style: str = "natural",
    site_type: str = "outdoor",
    title: str = "E2E KO",
) -> Tuple[KnowledgeObject, VersionStore, EvolutionAuditStore]:
    """Run the full V1 chain with custom proposal fields.

    ``_run_e2e_happy`` does not expose ``proposal_overrides``;
    this helper threads the override through
    ``_build_admission_candidate`` for multi-corpus cases
    where each KO must carry distinct theme / style /
    site_type values.
    """
    raw = _build_raw_case(title=title)
    case = _build_case_knowledge(raw)

    promotion = _build_promotion_candidate(
        case, proposed_knowledge_id=target_id,
    )
    checker = PromotionEligibilityChecker()
    _, promotion_eligible = checker.check(promotion)

    admission = _build_admission_candidate(
        promotion_eligible,
        target_knowledge_id=target_id,
        proposal_overrides={
            "title": title,
            "theme": theme,
            "style": style,
            "site_type": site_type,
        },
    )
    admission_checker = AdmissionChecker()
    _, admission_eligible = admission_checker.check(admission)

    version_store = VersionStore()
    audit_store = EvolutionAuditStore()
    writer = AdmissionWriter(
        version_store=version_store,
        audit_store=audit_store,
        on_duplicate="idempotent",
    )
    wr = writer.write(admission_eligible)
    assert wr.status == CREATED
    assert wr.knowledge_object is not None
    return wr.knowledge_object, version_store, audit_store


def _build_rejected_admission() -> AdmissionCandidate:
    """Build an AdmissionCandidate that AdmissionChecker
    rejects with NOT_ADMISSIBLE (rule A8: missing
    ``human_review_marker`` in justification)."""
    raw = _build_raw_case()
    case = _build_case_knowledge(raw)

    promotion = _build_promotion_candidate(case)
    checker = PromotionEligibilityChecker()
    _, promotion_eligible = checker.check(promotion)

    return new_admission_candidate(
        promotion_candidate_id=promotion_eligible.candidate_id,
        case_id=promotion_eligible.case_id,
        case_source_kind=promotion_eligible.case_source_kind,
        provenance_chain=_build_provenance_chain(),
        target_knowledge_id="ko_rejected_v1",
        admission_proposal=_build_admission_proposal(),
        justification="",  # A8_human_review_marker_present fires
        requires_human_review=True,
        created_by="e2e_test",
    )


def _terminal_request_for_forest() -> TerminalRequest:
    """TerminalRequest that aligns with the 25.4-B default
    forest admission proposal (site_type=outdoor,
    theme=forest, style=natural)."""
    return TerminalRequest(
        site_type="outdoor",
        site_description="kindergarten playground 3-6 forest",
        preferred_theme="forest",
        preferred_style="natural",
    )


# ===========================================================================
# 1. Happy path: single KO from admission -> Terminal retrieve
# ===========================================================================


class TestAdmissionToTerminalHappyPath:
    """Single KO produced by AdmissionWriter is consumable by
    TerminalService."""

    def test_single_ko_retrieved_by_structured_filters(self):
        out = _run_e2e_happy()
        ko = out["write_result"].knowledge_object
        assert ko is not None
        assert ko.knowledge_id == FOREST_KO_ID

        svc = TerminalService()
        result = svc.execute(_terminal_request_for_forest(), [ko])

        assert result.success is True
        assert result.failure_reason == ""
        assert result.total_hits == 1
        hit = result.cases[0]
        assert hit.knowledge_id == FOREST_KO_ID
        assert hit.knowledge_version == 1

    def test_single_ko_retrieved_by_query_text(self):
        """Without preferred_theme / preferred_style the
        query_text drives the match via KO title / description."""
        out = _run_e2e_happy()
        ko = out["write_result"].knowledge_object
        assert ko is not None

        req = TerminalRequest(
            site_type="outdoor",
            site_description="forest kindergarten case from operator intake",
            preferred_theme="",
            preferred_style="",
        )
        result = TerminalService().execute(req, [ko])

        assert result.success is True
        assert result.total_hits >= 1
        assert result.cases[0].knowledge_id == FOREST_KO_ID

    def test_match_score_above_threshold(self):
        """Fully-aligned request (theme + style + site_type)
        yields a meaningful match_score on the forest KO."""
        out = _run_e2e_happy()
        ko = out["write_result"].knowledge_object
        assert ko is not None

        result = TerminalService().execute(
            _terminal_request_for_forest(), [ko],
        )
        assert result.total_hits == 1
        assert result.cases[0].match_score >= 0.5


# ===========================================================================
# 2. Multi-corpus: 3 admitted KOs -> Terminal filters
# ===========================================================================


class TestAdmissionToTerminalMultiCorpus:
    """Multiple KOs admitted independently -> Terminal filters
    by the V1 structured constraints (site_type / theme / style)."""

    def test_three_admissions_filter_to_one_theme(self):
        """3 KOs with distinct themes; preferred_theme=forest
        yields exactly the forest KO."""
        ko_forest, _, _ = _build_one_admission_with_overrides(
            FOREST_KO_ID, theme="forest", title="Forest kindergarten",
        )
        ko_ocean, _, _ = _build_one_admission_with_overrides(
            OCEAN_KO_ID, theme="ocean", title="Ocean kindergarten",
        )
        ko_urban, _, _ = _build_one_admission_with_overrides(
            URBAN_KO_ID, theme="urban", title="Urban kindergarten",
        )

        req = TerminalRequest(
            site_type="outdoor",
            site_description="kindergarten playground",
            preferred_theme="forest",
            preferred_style="natural",
        )
        result = TerminalService().execute(
            req, [ko_forest, ko_ocean, ko_urban],
        )
        assert result.success is True
        assert result.total_hits == 1
        assert result.cases[0].knowledge_id == FOREST_KO_ID

    def test_three_admissions_all_visible_without_theme_filter(self):
        """3 KOs with shared site_type; no theme / style filter
        -> all 3 are returned (within default limit 5)."""
        ko1, _, _ = _build_one_admission_with_overrides(
            FOREST_KO_ID, theme="forest", site_type="outdoor",
            title="Forest outdoor",
        )
        ko2, _, _ = _build_one_admission_with_overrides(
            OCEAN_KO_ID, theme="ocean", site_type="outdoor",
            title="Ocean outdoor",
        )
        ko3, _, _ = _build_one_admission_with_overrides(
            URBAN_KO_ID, theme="urban", site_type="outdoor",
            title="Urban outdoor",
        )

        req = TerminalRequest(
            site_type="outdoor",
            site_description="kindergarten playground",
            preferred_theme="",
            preferred_style="",
        )
        result = TerminalService().execute(req, [ko1, ko2, ko3])
        assert result.total_hits == 3
        ids = sorted(c.knowledge_id for c in result.cases)
        assert ids == sorted([FOREST_KO_ID, OCEAN_KO_ID, URBAN_KO_ID])


# ===========================================================================
# 3. Rejection paths: bad writer -> no corpus -> Terminal clean
# ===========================================================================


class TestAdmissionTerminalRejectionPaths:
    """When AdmissionWriter does not produce a KO, Terminal sees
    an empty corpus and returns total_hits=0."""

    def test_rejected_admission_yields_no_corpus(self):
        """NOT_ADMISSIBLE candidate -> writer REJECTED ->
        Terminal sees empty corpus -> total_hits=0."""
        bad = _build_rejected_admission()
        _, stamped = AdmissionChecker().check(bad)
        assert stamped.status == NOT_ADMISSIBLE

        vs = VersionStore()
        au = EvolutionAuditStore()
        writer = AdmissionWriter(
            version_store=vs, audit_store=au, on_duplicate="idempotent",
        )
        wr = writer.write(stamped)
        assert wr.status == REJECTED
        assert wr.knowledge_object is None

        result = TerminalService().execute(
            _terminal_request_for_forest(), [],
        )
        assert result.success is True
        assert result.total_hits == 0
        assert len(result.cases) == 0

    def test_idempotent_duplicate_does_not_create_new_ko(self):
        """Second write against an existing identity returns
        IDEMPOTENT (knowledge_object=None). Terminal still sees
        only the originally admitted KO."""
        out1 = _run_e2e_happy()
        ko1 = out1["write_result"].knowledge_object
        assert ko1 is not None

        out2 = _run_e2e_happy()
        shared_writer = AdmissionWriter(
            version_store=out1["version_store"],
            audit_store=out1["audit_store"],
            on_duplicate="idempotent",
        )
        wr = shared_writer.write(out2["admission_eligible"])
        assert wr.status == IDEMPOTENT
        assert wr.knowledge_object is None

        result = TerminalService().execute(
            _terminal_request_for_forest(), [ko1],
        )
        assert result.total_hits == 1
        assert result.cases[0].knowledge_id == FOREST_KO_ID

        # VersionStore baseline stays at v1 (single record).
        history = out1["version_store"].history(FOREST_KO_ID)
        assert len(history) == 1

    def test_strict_duplicate_raises(self):
        """on_duplicate='strict' raises DuplicateAdmissionError;
        Terminal is not invoked."""
        out1 = _run_e2e_happy()
        out2 = _run_e2e_happy()
        strict_writer = AdmissionWriter(
            version_store=out1["version_store"],
            audit_store=out1["audit_store"],
            on_duplicate="strict",
        )
        with pytest.raises(DuplicateAdmissionError):
            strict_writer.write(out2["admission_eligible"])


# ===========================================================================
# 4. Provenance / audit / version traceability across the boundary
# ===========================================================================


class TestAdmissionTerminalProvenanceAuditVersion:
    """VersionStore baseline + audit action=admission + Terminal
    hit version are all visible across the Terminal boundary."""

    def test_version_store_has_baseline(self):
        out = _run_e2e_happy()
        history = out["version_store"].history(FOREST_KO_ID)
        assert len(history) == 1
        baseline = history[0]
        assert baseline.version_number == 1
        assert baseline.previous_version is None
        assert baseline.target_identity == FOREST_KO_ID

    def test_audit_record_is_action_admission(self):
        out = _run_e2e_happy()
        all_audits = out["audit_store"].list()
        assert len(all_audits) >= 1
        assert any(r.action == "admission" for r in all_audits)
        admission_record = next(
            r for r in all_audits if r.action == "admission"
        )
        assert admission_record.after is not None
        assert admission_record.after.get("knowledge_id") == FOREST_KO_ID

    def test_terminal_hit_reflects_version_1(self):
        out = _run_e2e_happy()
        ko = out["write_result"].knowledge_object
        assert ko is not None

        result = TerminalService().execute(
            _terminal_request_for_forest(), [ko],
        )
        hit = result.cases[0]
        assert hit.knowledge_id == FOREST_KO_ID
        assert hit.knowledge_version == 1


# ===========================================================================
# 5. Architecture boundary AST
# ===========================================================================


class TestAdmissionTerminalArchitectureBoundary:
    """The E2E test file MUST NOT import forbidden modules."""

    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.brain",
        "caseos.knowledge.governance",
        "caseos.knowledge.feedback",
        "caseos.knowledge.corpus",
    )

    def test_no_forbidden_imports(self):
        here = Path(__file__).resolve()
        tree = ast.parse(here.read_text(encoding="utf-8"))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    if any(target.startswith(s)
                           for s in self.FORBIDDEN_SUBSTRINGS):
                        offenders.append((target, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if any(module.startswith(s)
                       for s in self.FORBIDDEN_SUBSTRINGS):
                    offenders.append((module, node.lineno))
        assert offenders == [], (
            "forbidden imports detected: " + repr(offenders)
        )