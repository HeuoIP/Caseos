"""Trust Module -- Sprint 19.3 runtime implementation (ADR-016).

Status:
    Replaces the Sprint 19.1 placeholder with the first real
    evidence-based evaluator. Reuses the rule pattern established
    by Sprint 19.2 (Decision Intelligence V1) but never produces
    High confidence in V1 -- per spec section 7, High requires
    expert confirmation, which is out of scope for Sprint 19.3.

Trust Object fields (ADR-016 Section 2 + Sprint 19.3 spec Section 2):
    1. evidence              what supports the decision
    2. source_reliability    how reliable the sources are (qualitative
                             labels; per ADR-016 the 5 labels
                             expert-verified / real-project-completed /
                             user-feedback / repeated-success /
                             theoretical-assumption)
    3. applicability_match   how well the evidence fits the project
    4. confidence            High | Medium | Low (V1 never emits High)
    5. uncertainty_handling  what remains unknown

The engine emits an additional `_trace` block (parity with the
Decision Engine) so an operator can replay why a given confidence
level was reached.

Constraint per spec section 7 (Confidence Rules V1):
    "No High confidence generation.
     High requires expert confirmation.
     Only Low / Medium are possible."
This module enforces the rule. A rule that would otherwise return
High is downgraded to Medium with an explicit caveat ("High requires
expert confirmation per ADR-016 Section 7").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


# Allowed V1 confidence labels (High is FORBIDDEN).
ALLOWED_LEVELS = ("Medium", "Low")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_rule_trace(decision: dict | None) -> bool:
    if not isinstance(decision, dict):
        return False
    trace = decision.get("_trace") or {}
    rid = trace.get("rule_id")
    return bool(rid) and rid != "None"


def _suitable_set(ko: dict) -> set[str]:
    """Return the set of project types this KO is suitable for."""
    app = ko.get("applicability") or {}
    if isinstance(app, dict):
        suitable = app.get("suitable") or app.get("suitable_when") or []
    else:
        suitable = []
    return {str(s) for s in suitable}


def _supporting_knowledge(project_type: str, knowledge_patterns: list[dict]) -> list[dict]:
    """Return KOs whose `applicability` lists include this project type."""
    out = []
    for ko in knowledge_patterns or []:
        if project_type in _suitable_set(ko):
            out.append(ko)
    return out


def _principle_text(ko: dict) -> str:
    return (ko.get("principle") or "").strip()


def _conflicts_with_decision(ko: dict, decision: dict) -> bool:
    r"""V1 contradiction heuristic.

    Returns True if the given FailurePattern KO contradicts the
    Decision's \decision\ field. The heuristic is intentionally
    conservative -- it only fires when the KO contains an explicit
    "do not <verb> <noun>" prohibition and the decision's \decision    text targets the same noun with a build/add verb.

    Future: ADR-018 will replace this with a real semantic comparison.
    The current V1 signals:

      (a) KO is a FailurePattern whose combined \principle + boundary          text says \do not <verb> <noun>\ and the decision text
          contains a build/add verb targeting that same noun.
      (b) KO is a FailurePattern whose combined text says
          \
emove before <add|build|create> <noun>\ AND the
          decision targets the SAME noun (i.e. \dd <noun>\ /
          \uild <noun>\ / \create <noun>\). Without a matching
          noun the rule stays silent -- e.g. a generic
          "remove before add" principle is NOT treated as a
          contradiction against a "create an experience" decision    """


    if not isinstance(decision, dict):
        return False
    identity = (ko.get("identity") or "").lower()
    if "failurepattern" not in identity:
        return False

    decision_text = (decision.get("decision") or "").lower()

    # KO side: tolerant of boundary being str or list[str].
    boundary_field = ko.get("boundary")
    if isinstance(boundary_field, list):
        boundary_text = " ".join(str(b) for b in boundary_field)
    elif isinstance(boundary_field, str):
        boundary_text = boundary_field
    else:
        boundary_text = ""
    principle_text = _principle_text(ko).lower()
    ko_text = f"{principle_text}  {boundary_text}".strip()

    def _has_build_verb_noun(verb_pattern: str, noun: str) -> bool:
        return bool(
            re.search(
                rf"\b{verb_pattern}\b.*\b{re.escape(noun)}\b",
                decision_text,
            )
        )

    # (a) "do not <verb> <noun>" in KO vs build verb + same noun in decision.
    m = re.search(r"\bdo not (\w+) (\w+)", ko_text)
    if m:
        blocked_verb, blocked_noun = m.group(1), m.group(2)
        if _has_build_verb_noun(r"(add|use|build|create|stack|scatter|place|drop)", blocked_noun):
            return True

    # (b) "remove before <add|build|create> <noun>" in KO; decision must
    #     mention the SAME noun with a build verb. This is the narrow
    #     "remove-before-add" matcher.
    m2 = re.search(
        r"\bremove (?:before|rather than) (?:add|build|create) (\w+)\b",
        ko_text,
    )
    if m2:
        blocked_noun = m2.group(1)
        if _has_build_verb_noun(r"(add|build|create|stack|scatter|place|drop)", blocked_noun):
            return True

    return False

# ---------------------------------------------------------------------------
# Rule base + three V1 rules
# ---------------------------------------------------------------------------

@dataclass
class TrustRule:
    """A transparent if-then trust rule.

    Mirrors the Decision Engine Rule shape (id / name / matches /
    apply). The apply() returns a *partial* Trust Object that the
    engine composes; rules that do not match contribute nothing.
    """

    id: str
    name: str

    def matches(self, decision: dict, knowledge_patterns: list[dict], project_type: str) -> bool:
        raise NotImplementedError

    def apply(
        self,
        decision: dict,
        knowledge_patterns: list[dict],
        project_type: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class RuleT01_FullEvidence(TrustRule):
    """Sprint 19.3 spec section 5 / Rule T-01.

    IF: decision has a valid rule trace
        AND supporting knowledge object exists for this project type
        AND applicability matches
    THEN: Confidence = Medium; Evidence populated.
    """

    id: str = "T-01"
    name: str = "Decision trace plus applicable supporting knowledge"

    def matches(self, decision, knowledge_patterns, project_type):
        if not _has_rule_trace(decision):
            return False
        supporting = _supporting_knowledge(project_type, knowledge_patterns)
        return bool(supporting)

    def apply(self, decision, knowledge_patterns, project_type):
        supporting = _supporting_knowledge(project_type, knowledge_patterns)
        identities = [ko.get("identity") for ko in supporting]
        return {
            "evidence": (
                "Decision supported by explicit reasoning rule and "
                "relevant knowledge object(s): " + ", ".join(
                    str(i) for i in identities if i
                )
            ),
            "source_reliability": ["real-project-completed"],
            "applicability_match": "high",
            "confidence": "Medium",
        }


@dataclass
class RuleT02_DecisionWithoutEvidence(TrustRule):
    """Spec section 5 / Rule T-02.

    IF: decision has a rule trace BUT no supporting knowledge
    THEN: Confidence = Low; uncertainty populated.
    """

    id: str = "T-02"
    name: str = "Decision trace but no supporting knowledge"

    def matches(self, decision, knowledge_patterns, project_type):
        if not _has_rule_trace(decision):
            return False
        return not _supporting_knowledge(project_type, knowledge_patterns)

    def apply(self, decision, knowledge_patterns, project_type):
        return {
            "evidence": (
                "Decision logic exists (rule trace present) but no "
                "knowledge object applies to this project type"
            ),
            "source_reliability": ["theoretical-assumption"],
            "applicability_match": "low",
            "confidence": "Low",
            "uncertainty_handling": [
                "Decision logic exists but supporting evidence is insufficient",
            ],
        }


@dataclass
class RuleT03_ContradictoryEvidence(TrustRule):
    """Spec section 5 / Rule T-03.

    IF: conflicting evidence exists
    THEN: Confidence = Low; uncertainty populated with the
          contradiction note.
    """

    id: str = "T-03"
    name: str = "Contradictory evidence detected"

    def matches(self, decision, knowledge_patterns, project_type):
        if not _has_rule_trace(decision):
            return False
        for ko in knowledge_patterns or []:
            if _conflicts_with_decision(ko, decision):
                return True
        return False

    def apply(self, decision, knowledge_patterns, project_type):
        conflicting = [
            ko.get("identity")
            for ko in (knowledge_patterns or [])
            if _conflicts_with_decision(ko, decision)
        ]
        return {
            "evidence": (
                "Available knowledge contains an entry that "
                "contradicts the proposed decision"
            ),
            "source_reliability": ["user-feedback"],  # contradiction surfaced
            "applicability_match": "medium",
            "confidence": "Low",
            "uncertainty_handling": [
                "Available evidence contains contradiction requiring further validation",
                f"conflicting_knowledge: {[c for c in conflicting if c]}",
            ],
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TrustEngine:
    """Orchestrates trust-rule evaluation against a Decision Object.

    Rule order matters. T-03 (contradiction) is checked first because
    a contradicting evidence chip should never be hidden behind a
    Medium-signal rule. Then T-01 fires for the full-evidence case.
    T-02 is the fallback when T-01 does not match.
    """

    def __init__(self, rules: list[TrustRule] | None = None) -> None:
        self.rules = rules or [
            RuleT03_ContradictoryEvidence(),
            RuleT01_FullEvidence(),
            RuleT02_DecisionWithoutEvidence(),
        ]

    def evaluate(
        self,
        decision: dict | None,
        knowledge_patterns: list[dict],
        project_type: str = "",
    ) -> dict[str, Any]:
        project_type = project_type or ""

        if not decision:
            return self._no_decision_object()

        # Stage-1: contradiction
        for rule in [r for r in self.rules if r.id == "T-03"]:
            if rule.matches(decision, knowledge_patterns, project_type):
                return self._finalise(rule, decision, knowledge_patterns, project_type)

        # Stage-2: full evidence
        for rule in [r for r in self.rules if r.id == "T-01"]:
            if rule.matches(decision, knowledge_patterns, project_type):
                return self._finalise(rule, decision, knowledge_patterns, project_type)

        # Stage-3: decision-without-evidence
        for rule in [r for r in self.rules if r.id == "T-02"]:
            if rule.matches(decision, knowledge_patterns, project_type):
                return self._finalise(rule, decision, knowledge_patterns, project_type)

        # Stage-4: no rule trace at all
        return self._no_rule_trace(decision)

    # -- internals --

    def _finalise(
        self,
        rule: TrustRule,
        decision: dict,
        knowledge_patterns: list[dict],
        project_type: str,
    ) -> dict[str, Any]:
        partial = rule.apply(decision, knowledge_patterns, project_type)
        # Enforce V1 confidence ceiling: High is FORBIDDEN.
        conf = partial.get("confidence", "Low")
        if conf not in ALLOWED_LEVELS:
            partial["confidence"] = "Medium"
            partial.setdefault("uncertainty_handling", []).append(
                "High confidence would have been issued but is forbidden "
                "in V1 (ADR-016 Section 7; requires expert confirmation)."
            )

        # Compose final Trust Object with the 5 ADR-016 fields.
        trust: dict[str, Any] = {
            "schema_version": "trust_object_v1",
            "evidence": partial.get("evidence", ""),
            "source_reliability": partial.get("source_reliability", []),
            "applicability_match": partial.get("applicability_match", "unknown"),
            "confidence": partial.get("confidence", "Low"),
            "uncertainty_handling": partial.get("uncertainty_handling", []),
        }

        # Always include a sample-of-knowledge caveat if any KO is loaded
        # but none matched project_type, so operators can see why Medium
        # did not become "high applicability match".
        supporting = _supporting_knowledge(project_type, knowledge_patterns)
        loaded_count = len(knowledge_patterns or [])
        if loaded_count and not supporting:
            trust["uncertainty_handling"] = (
                list(trust["uncertainty_handling"]) +
                [f"{loaded_count} knowledge object(s) loaded; none applicable to project_type '{project_type}'"]
            )

        # Spec section 10 / worked example: "No site image analysis
        # available yet."  is the canonical V1 caveat regardless of rule.
        trust["uncertainty_handling"] = list(trust["uncertainty_handling"]) + [
            "No site image analysis available yet (Vision engine is out of scope for Sprint 19.3).",
        ]

        # Trace block (parity with Decision Engine)
        trust["_trace"] = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_order": [r.id for r in self.rules],
            "knowledge_loaded_count": len(knowledge_patterns or []),
            "supporting_knowledge_count": len(supporting),
            "supporting_knowledge_identities": [
                ko.get("identity") for ko in supporting
            ],
            "project_type": project_type,
        }
        trust["_engine_version"] = "trust_engine_v1"
        return trust

    def _no_rule_trace(self, decision: dict) -> dict[str, Any]:
        return {
            "schema_version": "trust_object_v1",
            "evidence": "No decision trace available",
            "source_reliability": ["theoretical-assumption"],
            "applicability_match": "low",
            "confidence": "Low",
            "uncertainty_handling": [
                "Decision Object has no traceable rule. Cannot evaluate trust.",
                "No site image analysis available yet (Vision engine is out of scope for Sprint 19.3).",
            ],
            "_trace": {
                "rule_id": None,
                "rule_name": None,
                "rule_order": [r.id for r in self.rules],
                "knowledge_loaded_count": len([]),
                "supporting_knowledge_count": 0,
                "supporting_knowledge_identities": [],
                "project_type": "",
            },
            "_engine_version": "trust_engine_v1",
        }

    def _no_decision_object(self) -> dict[str, Any]:
        return {
            "schema_version": "trust_object_v1",
            "evidence": "No Decision Object was produced.",
            "source_reliability": [],
            "applicability_match": "unknown",
            "confidence": "Low",
            "uncertainty_handling": [
                "Trust cannot be evaluated without a Decision Object.",
                "No site image analysis available yet (Vision engine is out of scope for Sprint 19.3).",
            ],
            "_trace": {
                "rule_id": None,
                "rule_name": None,
                "rule_order": [r.id for r in self.rules],
                "knowledge_loaded_count": 0,
                "supporting_knowledge_count": 0,
                "supporting_knowledge_identities": [],
                "project_type": "",
            },
            "_engine_version": "trust_engine_v1",
        }


# ---------------------------------------------------------------------------
# Stage wrapper (pipeline wire contract preserved)
# ---------------------------------------------------------------------------

class TrustModule(Stage):
    """Pipeline stage: `trust`.

    Same Stage contract as the Sprint 19.1 placeholder; the actual
    evaluation moved into `TrustEngine`.
    """

    name = "trust"

    def __init__(self, engine: TrustEngine | None = None) -> None:
        self.engine = engine or TrustEngine()

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.trust_object = self.engine.evaluate(
            decision=ctx.decision_object,
            knowledge_patterns=ctx.knowledge_patterns,
            project_type=ctx.project.project_type,
        )
        return ctx


__all__ = [
    "TrustEngine",
    "TrustModule",
    "TrustRule",
    "RuleT01_FullEvidence",
    "RuleT02_DecisionWithoutEvidence",
    "RuleT03_ContradictoryEvidence",
    "ALLOWED_LEVELS",
]