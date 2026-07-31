"""Knowledge Retrieval Module -- Sprint 20 runtime implementation (ADR-019).

Status:
    First executable Evidence Retrieval layer. Replaces the previous
    pattern of "every stage reads the full knowledge_patterns list"
    with a dedicated retrieval stage that produces an Evidence
    Package per ADR-019.

Pipeline position (Sprint 20 spec section 8):

    Human -> Knowledge -> Retrieval -> Decision -> Trust -> Recommendation

Sprint 21 update:
    Optional `human_context` parameter on `RetrievalEngine.retrieve()`.
    Human keywords (user_goal / business_context / success_definition)
    contribute a *bounded* boost to the P1 applicability score when
    they overlap with a KO's applicability tags. The retrieval priority
    order P1 -> P2 -> P3 -> P4 is unchanged; the rule list remains
    RULE_APPLICABILITY = [P1, P2, P3, P4]. Per Sprint 21 spec section 6:

        "Do not change ADR-019 priority order. Retrieval priority
         remains: P1 Applicability, P2 Diagnosis, P3 Situation,
         P4 Boundary, P5 Visual similarity. Human context is
         additional applicability evidence."

Architectural principle (ADR-019 Section 2):

    CaseOS Retrieval is NOT "find similar images".
    CaseOS Retrieval IS  "find applicable knowledge evidence that
                          supports a spatial decision".

    Primary objective: Decision Applicability > Visual Similarity.

Evidence Package contract (ADR-019 Section 4) -- exactly 5 fields:

    1. relevant_objects       -- the KOs that matched
    2. applicability_reason   -- WHY each KO matches the current project
    3. supporting_principle   -- the design principle contributed
    4. boundary_warning       -- when this evidence should NOT be applied
    5. trust_contribution     -- how this evidence moves confidence

Retrieval priority model (ADR-019 Section 5, Sprint 20 spec section 6):

    P1 Decision applicability     (project_type in KO.suitable)
    P2 Diagnosis match             (decision.diagnosis keywords in KO)
    P3 Situation match             (project.site_description keywords in KO)
    P4 Boundary compatibility      (decision.boundary not violated by KO)
    P5 Visual similarity           (NOT IMPLEMENTED IN V1, per ADR-019)

Sprint 21 (ADR-013) adds a *bounded* P1 boost sourced from
HumanContext. The priority order is NOT changed; the boost is part
of P1's contribution. The rule list therefore stays P1..P4.

Constraints (Sprint 20 spec section 11, ADR-019 Section 10):

    * No vector database.
    * No embeddings.
    * No image search.
    * No LLM generation.
    * No frontend / user feed / social ranking.

The retrieval is *deterministic* and *testable*: every match
decision can be reproduced from inputs alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Score weights per ADR-019 Section 5. Visual similarity is P5 and is
# explicitly NOT IMPLEMENTED in V1.
SCORE_P1_APPLICABILITY = 100
SCORE_P2_DIAGNOSIS = 30
SCORE_P3_SITUATION = 20
SCORE_P4_BOUNDARY = 10
SCORE_THRESHOLD = 10  # KOs with score < threshold are not retrieved

# Sprint 21 (ADR-013): bounded HumanContext applicability boost.
# Human keywords that overlap with a KO's applicability tags add
# up to this many points to P1's contribution. The boost is part
# of P1 (NOT a new priority) so the rule list P1..P4 stays intact.
SCORE_HUMAN_BOOST_MAX = 15


# Stopwords used for keyword extraction. Small and explicit; the goal
# is "non-junk keyword overlap", not linguistic analysis.
_STOPWORDS = frozenset(
    """
    a an the of in on at to for from with and or but if is are was were be
    been being do does did has have had this that these those it its
    as by about into over under between up down out off
    """.split()
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keywords(text: str | None) -> set[str]:
    """Extract lowercase keywords (>3 chars, not stopwords)."""
    if not text:
        return set()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]+", str(text).lower())
    return {t for t in tokens if len(t) > 3 and t not in _STOPWORDS}


def _suitable_set(ko: dict) -> set[str]:
    """Return the set of project-type tags this KO is suitable for.

    Tolerant of both `suitable` and `suitable_when` (the two shapes
    used in the sample KOs).
    """
    app = ko.get("applicability") or {}
    if not isinstance(app, dict):
        return set()
    suitable = list(app.get("suitable") or []) + list(app.get("suitable_when") or [])
    return {str(s) for s in suitable}


def _applicability_match(ko: dict, project_type: str,
                         site_description: str = "") -> bool:
    """P1 hard filter.

    A KO is applicable if ANY of:
      (a) `project_type` is in KO.suitable
      (b) KO.suitable contains an `any_*` wildcard
      (c) KO.suitable_when has at least one keyword that overlaps
          with the project site_description (natural-language match)

    (c) is the P1b extension: it lets Decision Patterns with
    natural-language conditions (e.g. "site is open or under-defined")
    be retrieved when the project text contains overlapping words.
    """
    suitable = _suitable_set(ko)
    if not suitable:
        return False
    if project_type in suitable:
        return True
    for tag in suitable:
        if tag.startswith("any_") or tag == "any":
            return True
    # P1b: suitable_when keyword overlap with site_description.
    if site_description:
        site_kw = _keywords(site_description)
        for tag in suitable:
            tag_kw = _keywords(tag)
            if site_kw & tag_kw:
                return True
    return False


def _human_overlap_score(ko: dict, human_context: Mapping[str, Any] | None) -> int:
    """Sprint 21 / ADR-013: bounded applicability boost from HumanContext.

    The boost is sourced from these HumanContext fields:
        user_goal
        business_context
        success_definition

    For each KO we look at the *text* of its applicability tags
    (both `suitable` and `suitable_when`); if any of the human
    keywords overlap with that text, we add a small contribution
    (capped at SCORE_HUMAN_BOOST_MAX). The boost is reported as
    part of P1's contribution -- the rule list P1..P4 is unchanged.
    """
    if not human_context:
        return 0
    human_blob_parts: list[str] = []
    for field_name in ("user_goal", "business_context", "success_definition"):
        v = human_context.get(field_name)
        if isinstance(v, str) and v.strip() and v.strip() != "__UNKNOWN__":
            human_blob_parts.append(v)
    if not human_blob_parts:
        return 0
    human_kw = _keywords(" ".join(human_blob_parts))
    if not human_kw:
        return 0

    # KO side: suitability text + principle/decision keywords.
    suitable = _suitable_set(ko)
    tag_blob = " ".join(suitable)
    ko_blob = tag_blob + " " + str(ko.get("principle", "") or "") + " " + \
        " ".join(str(x) for x in (ko.get("decision") or []) if isinstance(x, str))
    ko_kw = _keywords(ko_blob)
    overlap = human_kw & ko_kw
    if not overlap:
        return 0
    # Layered: 1 overlap -> +5, 2 -> +10, 3+ -> +15 (cap).
    if len(overlap) >= 3:
        return SCORE_HUMAN_BOOST_MAX
    if len(overlap) == 2:
        return min(SCORE_HUMAN_BOOST_MAX, 10)
    return min(SCORE_HUMAN_BOOST_MAX, 5)


def _ko_text_blob(ko: dict) -> str:
    """All free-text fields of a KO concatenated for keyword overlap."""
    parts: list[str] = []
    for key in (
        "principle",
        "diagnosis",
        "decision",
        "situation",
        "situation_context",
        "observation",
        "feedback",
    ):
        v = ko.get(key)
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(x) for x in v)
    return " ".join(parts)


def _boundary_warnings(ko: dict) -> list[str]:
    """Return the boundary list as strings (handles str or list)."""
    b = ko.get("boundary")
    if isinstance(b, list):
        return [str(x) for x in b if x]
    if isinstance(b, str) and b.strip():
        return [b.strip()]
    return []


def _contradicts_decision(ko: dict, decision: dict) -> bool:
    r"""V1 contradiction heuristic.

    Returns True if the given FailurePattern KO contradicts the
    Decision's `decision` field. The heuristic is intentionally
    conservative -- it only fires when the KO contains an explicit
    "do not <verb> <noun>" prohibition and the decision's `decision`
    text targets the same noun with a build/add verb.

    See ADR-019 / Sprint 20 spec for the full heuristic.
    """
    if not isinstance(decision, dict):
        return False
    identity = (ko.get("identity") or "").lower()
    if "failurepattern" not in identity:
        return False

    decision_text = (decision.get("decision") or "").lower()

    boundary_field = ko.get("boundary")
    if isinstance(boundary_field, list):
        boundary_text = " ".join(str(b) for b in boundary_field)
    elif isinstance(boundary_field, str):
        boundary_text = boundary_field
    else:
        boundary_text = ""
    principle_text = _principle_text(ko).lower()
    ko_text = f"{principle_text}  {boundary_text}".strip()

    def _has_do_not(verb: str, noun: str) -> bool:
        return bool(re.search(
            rf"\bdo\s*not\s+{verb}\b[^\.]*\b{re.escape(noun)}\b",
            ko_text,
        ))

    def _has_remove_before(verb: str, noun: str) -> bool:
        return bool(re.search(
            rf"\bremove\s+before\s+{verb}\b[^\.]*\b{re.escape(noun)}\b",
            ko_text,
        ))

    m = re.search(r"\bdo\s*not\s+([a-z]+)\b[^\.]*\b([a-z][a-z\-]+)\b", ko_text)
    if m:
        verb, noun = m.group(1), m.group(2)
        if re.search(rf"\b(add|build|create|stack|scatter|place|drop)\b.*\b{re.escape(noun)}\b",
                    decision_text):
            return True

    m2 = re.search(r"\bremove\s+before\s+([a-z]+)\b[^\.]*\b([a-z][a-z\-]+)\b", ko_text)
    if m2:
        verb, noun = m2.group(1), m2.group(2)
        if re.search(
            rf"\b(add|build|create|stack|scatter|place|drop)\b.*\b{re.escape(noun)}\b",
            decision_text,
        ):
            return True
    return False


def _principle_text(ko: dict) -> str:
    return (ko.get("principle") or "").strip()


# ---------------------------------------------------------------------------
# Evidence Package (data contract)
# ---------------------------------------------------------------------------

@dataclass
class EvidencePackage:
    """The 5-field retrieval output per ADR-019 Section 4.

    `relevant_objects` is the only list field; the other four are
    narrative strings chosen from the highest-scoring KO (or an
    honest "no evidence" message if the retrieval is empty).
    """

    relevant_objects: list[dict]
    applicability_reason: str
    supporting_principle: str
    boundary_warning: str
    trust_contribution: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "evidence_package_v1",
            "relevant_objects": list(self.relevant_objects),
            "applicability_reason": self.applicability_reason,
            "supporting_principle": self.supporting_principle,
            "boundary_warning": self.boundary_warning,
            "trust_contribution": self.trust_contribution,
        }

    @classmethod
    def empty(cls) -> "EvidencePackage":
        return cls(
            relevant_objects=[],
            applicability_reason=(
                "No applicable Knowledge Objects were found for this project."
            ),
            supporting_principle="No supporting principle available.",
            boundary_warning="No boundary warning available.",
            trust_contribution=(
                "No evidence found; trust must default to Low until evidence arrives."
            ),
        )


# ---------------------------------------------------------------------------
# Rule base + four V1 priority rules
# ---------------------------------------------------------------------------

@dataclass
class RetrievalRule:
    """A single transparent scoring rule.

    Each rule inspects one priority dimension and returns an integer
    score contribution. Rules compose additively: a KO\'s total score
    is the sum of its matched-rule contributions. Rules that do not
    match contribute zero. KOs with total >= SCORE_THRESHOLD are
    included in the Evidence Package.
    """

    id: str
    name: str
    priority: int

    def score(
        self,
        ko: dict,
        project,
        decision: dict | None,
    ) -> int:
        raise NotImplementedError


@dataclass
class RuleP1_Applicability(RetrievalRule):
    """P1 -- project_type is in KO.suitable.

    Per ADR-019 Section 5, applicability is the primary ranking factor.
    This rule gates retrieval: a KO that fails P1 is excluded entirely
    (other rules can only add to a P1-passing base).
    """

    id: str = "P1"
    name: str = "Decision applicability"
    priority: int = 1

    def score(self, ko, project, decision) -> int:
        site = getattr(project, "site_description", "") or ""
        if not _applicability_match(ko, project.project_type, site):
            return 0
        return SCORE_P1_APPLICABILITY


@dataclass
class RuleP2_Diagnosis(RetrievalRule):
    """P2 -- decision.diagnosis keywords overlap with KO text."""

    id: str = "P2"
    name: str = "Diagnosis match"
    priority: int = 2

    def score(self, ko, project, decision) -> int:
        if not isinstance(decision, dict):
            return 0
        diag_kw = _keywords(decision.get("diagnosis", ""))
        if not diag_kw:
            return 0
        ko_kw = _keywords(_ko_text_blob(ko))
        if diag_kw & ko_kw:
            return SCORE_P2_DIAGNOSIS
        return 0


@dataclass
class RuleP3_Situation(RetrievalRule):
    """P3 -- project.site_description keywords overlap with KO text."""

    id: str = "P3"
    name: str = "Situation match"
    priority: int = 3

    def score(self, ko, project, decision) -> int:
        site_kw = _keywords(getattr(project, "site_description", ""))
        if not site_kw:
            return 0
        ko_kw = _keywords(_ko_text_blob(ko))
        if site_kw & ko_kw:
            return SCORE_P3_SITUATION
        return 0


@dataclass
class RuleP4_Boundary(RetrievalRule):
    """P4 -- the decision is not contradicted by the KO.

    This rule contributes a positive score for KOs that are
    compatible with the decision\'s boundary; KOs that contradict
    the decision are excluded at a higher layer (see
    `_contradicts_decision`).
    """

    id: str = "P4"
    name: str = "Boundary compatibility"
    priority: int = 4

    def score(self, ko, project, decision) -> int:
        if not isinstance(decision, dict):
            return 0
        if _contradicts_decision(ko, decision):
            return 0
        # Only award the P4 contribution if the KO actually carries
        # a boundary (otherwise the score would be noisy).
        if _boundary_warnings(ko):
            return SCORE_P4_BOUNDARY
        return 0


# Default rule list in P1 -> P4 order. P5 (visual similarity) is
# not implemented in V1 per ADR-019 Section 10.
RULE_APPLICABILITY: list[RetrievalRule] = [
    RuleP1_Applicability(),
    RuleP2_Diagnosis(),
    RuleP3_Situation(),
    RuleP4_Boundary(),
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RetrievalEngine:
    """Score + rank + package Knowledge Objects for the pipeline.

    The engine is intentionally tiny: it walks the rule list once per
    KO and ranks by total score. KOs that fail P1 (applicability)
    or that contradict the decision\'s boundary are excluded. KOs
    that fall below SCORE_THRESHOLD are also excluded. The top-scoring
    KO is the source of the package\'s narrative fields.

    Sprint 21 (ADR-013) update: `human_context` is an optional
    argument. When provided, it boosts the P1 contribution by up
    to `SCORE_HUMAN_BOOST_MAX` points. The priority order P1..P4
    is unchanged; the rule list is unchanged.
    """

    def __init__(self, rules: list[RetrievalRule] | None = None) -> None:
        self.rules = rules or RULE_APPLICABILITY

    def retrieve(
        self,
        project,
        decision: dict | None,
        knowledge_patterns: list[dict] | None,
        human_context: Mapping[str, Any] | None = None,
    ) -> EvidencePackage:
        knowledge_patterns = knowledge_patterns or []
        decision = decision or {}

        scored: list[tuple[int, dict, dict[str, int]]] = []
        for ko in knowledge_patterns:
            if not isinstance(ko, dict):
                continue
            # P1 hard filter: applicability first. If P1 fails, the
            # KO is not retrieved regardless of how high the other
            # rules score.
            p1 = self.rules[0].score(ko, project, decision)
            if p1 == 0:
                continue
            contributions = {"P1": p1}
            total = p1
            # Sprint 21 / ADR-013: bounded human-context boost.
            # Contributes to P1\'s reported contribution so the rule
            # list P1..P4 stays intact and the priority order is
            # preserved.
            if human_context is not None:
                hb = _human_overlap_score(ko, human_context)
                if hb:
                    contributions["P1"] = contributions["P1"] + hb
                    total += hb
            for rule in self.rules[1:]:
                c = rule.score(ko, project, decision)
                if c:
                    contributions[rule.id] = c
                    total += c
            if total >= SCORE_THRESHOLD:
                scored.append((total, ko, contributions))

        # Sort: highest score first; stable so equal scores preserve
        # corpus order.
        scored.sort(key=lambda t: t[0], reverse=True)

        if not scored:
            return EvidencePackage.empty()

        # Package shape: relevant_objects is the full ranked list.
        # The narrative fields are sourced from the top-scoring KO.
        relevant = [ko for (_score, ko, _c) in scored]
        top_ko = relevant[0]
        top_contributions = scored[0][2]

        # Build the applicability reason: list the matched P1 tag(s)
        # + the contributing rules. This makes the reason auditable.
        matched_tags = sorted(_suitable_set(top_ko) - {"any", "any_"})
        p1_reasons = ", ".join(matched_tags) if matched_tags else "(wildcard)"
        contrib_str = ", ".join(
            f"{rid}={c}" for rid, c in sorted(top_contributions.items())
        )
        applicability_reason = (
            f"Project type matches applicability tags: {p1_reasons}. "
            f"Contributing rules: {contrib_str}."
        )

        # Supporting principle: KO\'s principle, verbatim.
        supporting_principle = (top_ko.get("principle") or "").strip()
        if not supporting_principle:
            supporting_principle = (
                "Knowledge Object matched applicability but carried no principle."
            )

        # Boundary warning: KO\'s boundary list, joined; "None" if empty.
        boundaries = _boundary_warnings(top_ko)
        if boundaries:
            boundary_warning = " | ".join(boundaries)
        else:
            boundary_warning = "No explicit boundary on this evidence."

        # Trust contribution: classify the KO by identity prefix.
        identity = (top_ko.get("identity") or "").lower()
        if "golden" in identity or "golden_case" in identity:
            trust_contribution = (
                "Evidence from a real-project completed case "
                "(Golden Case) -- raises confidence ceiling."
            )
        elif "decisionpattern" in identity:
            trust_contribution = (
                "Evidence from a Decision Pattern -- a reusable "
                "judgment structure that raises applicability."
            )
        elif "expertprinciple" in identity:
            trust_contribution = (
                "Evidence from an Expert Principle -- raises "
                "reasoning quality."
            )
        elif "failurepattern" in identity:
            trust_contribution = (
                "Evidence from a Failure Pattern -- lowers confidence "
                "and warns of anti-target."
            )
        elif "userpreference" in identity:
            trust_contribution = (
                "Evidence from a User Preference -- raises human "
                "alignment."
            )
        else:
            trust_contribution = (
                "Evidence from an unclassified Knowledge Object -- "
                "applicability confirmed but source type unverified."
            )

        return EvidencePackage(
            relevant_objects=relevant,
            applicability_reason=applicability_reason,
            supporting_principle=supporting_principle,
            boundary_warning=boundary_warning,
            trust_contribution=trust_contribution,
        )


# ---------------------------------------------------------------------------
# Stage wrapper (pipeline wire contract preserved)
# ---------------------------------------------------------------------------

class KnowledgeRetriever(Stage):
    """Pipeline stage: `retrieval`.

    Position (Sprint 20 spec section 8): immediately after the
    `knowledge` stage, immediately before the `decision` stage.
    Writes `ctx.evidence_package`.

    Sprint 21 (ADR-013) update: forwards `ctx.human_context` to the
    retrieval engine so that the bounded human-context applicability
    boost can be applied. Backward-compatible: the engine treats
    `None` as "no human context available".
    """

    name = "retrieval"

    def __init__(self, engine: RetrievalEngine | None = None) -> None:
        self.engine = engine or RetrievalEngine()

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ep = self.engine.retrieve(
            project=ctx.project,
            decision=ctx.decision_object,
            knowledge_patterns=ctx.knowledge_patterns,
            human_context=ctx.human_context,
        )
        ctx.evidence_package = ep.to_dict()
        ctx.metadata["evidence_package_relevant_count"] = len(ep.relevant_objects)
        ctx.metadata["retrieval_rule_id"] = (
            "P1" if ep.relevant_objects else "NONE"
        )
        ctx.metadata["retrieval_human_context_used"] = (
            ctx.human_context is not None
        )
        return ctx


__all__ = [
    "EvidencePackage",
    "KnowledgeRetriever",
    "RetrievalEngine",
    "RetrievalRule",
    "RuleP1_Applicability",
    "RuleP2_Diagnosis",
    "RuleP3_Situation",
    "RuleP4_Boundary",
    "RULE_APPLICABILITY",
    "SCORE_HUMAN_BOOST_MAX",
]
