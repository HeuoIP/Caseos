"""Decision Module -- Sprint 19.2 runtime implementation.

Status:
    Replaces the Sprint 19.1 placeholder with the first real reasoning
    implementation per ADR-014 Decision Intelligence Model V1.

Composition:
    - DecisionEngine -- coordinates rule evaluation against signals.
    - Rule           -- a single transparent if-then reasoning unit.
    - Three V1 rules (RuleR1 / RuleR2 / RuleR3) implementing the
      explicit cases defined in the Sprint 19.2 spec section 4.
    - DecisionModule -- Stage subclass, exposed as `decision` stage.
      Same name and signature as the Sprint 19.1 placeholder so the
      pipeline does not need to change.

Decision Object field naming (Sprint 19.2 spec section 2 -- 7 fields):

    1. situation     what is happening?
    2. observation   what is visible or known?
    3. diagnosis     what is the underlying problem?
    4. decision      what should be prioritised?
    5. reasoning     why this decision?  (includes rule id + trace)
    6. boundary      what should NOT be done?
    7. applicability when does this decision apply?

Field-name mapping to ADR-014 (Decision Intelligence Model V1):

    Sprint 19.2   ADR-014 V1
    -----------    ---------------------
    situation     <- problem        (the user's stated issue)
    observation   <- evidence       (the cues we picked up from signals)
    diagnosis     <- priority       + root cause of the situation
    decision      <- strategy       + experience logic
    reasoning     <- reasoning      (now contains traceable rule id)
    boundary      <- boundaries     (a single field per Sprint 19.2)
    applicability <- strategy context (when this decision transfers)

The runtime keeps the Sprint 19.2 names because the downstream
Recommendation stage (Sprint 19.1 placeholder) already reads them
under those names; ADR-014's wording is documented here for ADR
cross-reference. Future Sprint 19.x may rename one or both layers
via an ADR.

Constraint:
    Per spec section 10, this module MUST NOT call any LLM, vision
    model, embedding service, database, or UI. Reasoning is
    transparent: every output cites the rule id that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------

# Each entry is a list of regexes; signal fires if any regex hits.
# Regexes are full anchors would over-fit; we use case-insensitive
# partial matches with at most one intervening token (e.g. "lacks a
# memorable identity", "lacks the theme") so spec wording and natural
# paraphrase both surface.
import re as _re


_SIGNAL_PATTERNS = {
    "lack_identity": [
        r"\blacks? identity\b",
        r"\bno identity\b",
        r"\bno memorable\b",
        r"\blacks? (a|the)? ?(memorable )?(identity|theme)\b",
        r"\black of (identity|theme|memorable)\b",
        r"\bno (clear )?(identity|theme|story)\b",
    ],
    "equipment_exists": [
        r"\b(existing|has some) (equipment|facilities)\b",
    ],
    "overloaded": [
        r"\boverloaded\b",
        r"\bscattered equipment\b",
        r"\btoo many facilities\b",
        r"\bvisual disorder\b",
        r"\black of hierarchy\b",
        r"\black of visual hierarchy\b",
    ],
    "budget_limited": [
        r"\b(limited|low|tight|constrained) budget\b",
        r"\blimited\b",
    ],
    "requests_large_facility": [
        r"\b(landmark|expensive) (facility|landmark)\b",
        r"\b(high-end|luxury|premium) facility\b",
        r"\blarge facility\b",
    ],
}


_COMPILED = {
    sig: [_re.compile(p, _re.IGNORECASE) for p in patterns]
    for sig, patterns in _SIGNAL_PATTERNS.items()
}


def _any_match(haystack: str, signal: str) -> bool:
    h = haystack or ""
    return any(p.search(h) for p in _COMPILED.get(signal, []))


def _extract_signals(
    project, human_context, knowledge_patterns
) -> dict[str, bool]:
    """Reduce the pipeline context to a flat boolean signal map.

    Returns a dict of `signal_name -> bool`. Each rule inspects only
    the signals it cares about; signals are deliberately cheap so the
    rules themselves can stay short and inspectable.
    """

    site = (project.site_description or "")
    goal = (project.user_goal or "")
    constraints = (project.constraints or "")
    budget_field = ""
    if isinstance(project.extras, dict):
        budget_field = str(project.extras.get("budget") or "")

    human_blob = " ".join(
        str(v) for v in (human_context or {}).values() if isinstance(v, str)
    )

    # Patterns may carry their own textual content too.
    pattern_blob = " ".join(
        str(p.get("diagnosis", "")) + " " + str(p.get("principle", ""))
        for p in (knowledge_patterns or [])
    )

    blob = " ".join([site, goal, constraints, budget_field, human_blob, pattern_blob])

    return {
        "space_problem_lack_of_identity":
            _any_match(site, "lack_identity")
            or _any_match(goal, "lack_identity"),
        "equipment_exists":
            _any_match(site, "equipment_exists"),
        "existing_space_overloaded":
            _any_match(site, "overloaded")
            or _any_match(pattern_blob, "overloaded"),
        "budget_limited":
            _any_match(constraints, "budget_limited")
            or _any_match(budget_field, "budget_limited"),
        "user_requests_large_facility":
            _any_match(goal, "requests_large_facility")
            or _any_match(human_blob, "requests_large_facility"),
    }


# ---------------------------------------------------------------------------
# Rule base + three V1 rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    """A transparent if-then reasoning unit.

    Each Rule is responsible for one slice of the design problem and
    carries an `id` + `name` that propagate into the Decision Object's
    `reasoning` field so the recommendation is traceable.
    """

    id: str
    name: str

    def matches(self, signals: dict[str, bool]) -> bool:
        raise NotImplementedError

    def apply(self, signals: dict[str, bool]) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class RuleR1_LackIdentityWithEquipment(Rule):
    """Spec section 4 / Rule 1.

    IF space lacks identity AND equipment already exists:
        diagnosis = not insufficient equipment but lack of narrative
        decision  = create experience anchor
        boundary  = do not add scattered equipment
    """

    id: str = "R-01"
    name: str = "Space lacks identity; equipment already exists"

    def matches(self, signals: dict[str, bool]) -> bool:
        return signals.get("space_problem_lack_of_identity", False) \
            and signals.get("equipment_exists", False)

    def apply(self, signals: dict[str, bool]) -> dict[str, Any]:
        return {
            "situation": (
                "user states the space has no clear identity; some "
                "equipment already exists on site"
            ),
            "observation": (
                "site description mentions an existing facility but no "
                "narrative or theme"
            ),
            "diagnosis": (
                "the problem is not insufficient equipment but a lack "
                "of spatial narrative"
            ),
            "decision": "Create a single thematically anchored experience",
            "reasoning": (
                f"Rule {self.id} fired: space_problem_lack_of_identity "
                f"AND equipment_exists -> prior experience anchor over "
                f"equipment addition"
            ),
            "boundary": "Do not add scattered, disconnected equipment",
            "applicability": (
                "Suitable for renewal / re-theming projects where some "
                "equipment already exists and identity is the gap"
            ),
        }


@dataclass
class RuleR2_BudgetConflictWithLargeFacility(Rule):
    """Spec section 4 / Rule 2.

    IF budget is limited AND user requests a large facility:
        decision  = prioritise spatial strategy before equipment
        boundary  = do not recommend expensive landmark without validation
    """

    id: str = "R-02"
    name: str = "Budget limited; user requests large facility"

    def matches(self, signals: dict[str, bool]) -> bool:
        return signals.get("budget_limited", False) \
            and signals.get("user_requests_large_facility", False)

    def apply(self, signals: dict[str, bool]) -> dict[str, Any]:
        return {
            "situation": (
                "the user is asking for a landmark-scale facility "
                "while budget is explicitly constrained"
            ),
            "observation": (
                "goal text names a large / landmark / luxury facility; "
                "constraints or budget field records a limited envelope"
            ),
            "diagnosis": (
                "treating the request at face value would commit budget "
                "to a single object before strategy is settled"
            ),
            "decision": (
                "Prioritise spatial strategy and validation before any "
                "equipment investment"
            ),
            "reasoning": (
                f"Rule {self.id} fired: budget_limited AND "
                f"user_requests_large_facility -> refuse to skip "
                f"strategy phase; protect core value first (per "
                f"Constitution Principle 003 and ADR-014 Principle 3)"
            ),
            "boundary": (
                "Do not recommend an expensive landmark facility without "
                "validation of fit and budget"
            ),
            "applicability": (
                "Suitable whenever budget and ambition are in tension; "
                "forces an escalation step rather than an automated "
                "decision"
            ),
        }


@dataclass
class RuleR3_OverloadedSpace(Rule):
    """Spec section 4 / Rule 3.

    IF existing space is overloaded:
        diagnosis = visual hierarchy problem
        decision  = remove before adding
    """

    id: str = "R-03"
    name: str = "Existing space is overloaded"

    def matches(self, signals: dict[str, bool]) -> bool:
        return signals.get("existing_space_overloaded", False)

    def apply(self, signals: dict[str, bool]) -> dict[str, Any]:
        return {
            "situation": (
                "the existing space shows signs of over-use or "
                "disorganised accumulation"
            ),
            "observation": (
                "site description and known failure-pattern knowledge "
                "mention overload, scattered equipment, or lack of "
                "hierarchy"
            ),
            "diagnosis": (
                "the symptom is visual disorder caused by too many "
                "elements competing for attention"
            ),
            "decision": "Remove before adding; establish hierarchy first",
            "reasoning": (
                f"Rule {self.id} fired: existing_space_overloaded -> "
                f"consolidation > addition (Constitution Section 4 "
                f"item 1: 'Never cover a weakness with a random "
                f"object')"
            ),
            "boundary": "Do not propose new facilities until removal is planned",
            "applicability": (
                "Suitable when site description or knowledge patterns "
                "flag overload, regardless of project type"
            ),
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DecisionEngine:
    """Coordinates rule evaluation against a signal map.

    The engine is intentionally tiny: it walks an ordered rule list
    and returns the first match. Order matters -- the most specific
    rules (R-01, R-02) precede the more general R-03 so a noisy site
    description does not get masked as a generic overload case.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or [
            RuleR1_LackIdentityWithEquipment(),
            RuleR2_BudgetConflictWithLargeFacility(),
            RuleR3_OverloadedSpace(),
        ]

    def decide(
        self,
        project,
        human_context,
        knowledge_patterns,
    ) -> dict[str, Any]:
        signals = _extract_signals(project, human_context, knowledge_patterns)
        fired = [r for r in self.rules if r.matches(signals)]
        if not fired:
            return self._more_information_required(signals)
        # First match wins for the headline decision; later matches become
        # additional reasoning lines so multiple concerns surface.
        primary = fired[0]
        out = primary.apply(signals)
        if len(fired) > 1:
            extras = [
                f"additional rule fired: {r.id} ({r.name})"
                for r in fired[1:]
            ]
            out["reasoning"] = out["reasoning"] + "\n" + "\n".join(extras)
        out["_trace"] = {
            "rule_id": primary.id,
            "rule_name": primary.name,
            "signals": {k: bool(v) for k, v in signals.items()},
            "all_matched_rules": [r.id for r in fired],
        }
        out["_engine_version"] = "decision_engine_v1"
        out["_matched_signals"] = {
            k: True for k, v in signals.items() if v
        }
        return out

    def _more_information_required(self, signals: dict[str, bool]) -> dict[str, Any]:
        """ADR-014 Principle 5: a Decision is allowed to refuse.

        Mirrors the Constitution's "understand before recommending"
        and the Decision Principles' "Decision before Design".
        """

        return {
            "situation": "the available signals do not yet warrant a decision",
            "observation": (
                "no V1 rule matched the extracted signal set; further "
                "input is required"
            ),
            "diagnosis": "insufficient information to recommend",
            "decision": "More information required",
            "reasoning": (
                "No V1 rule matched the signal map "
                f"({list(signals)}). Per ADR-014 Principle 5 the "
                "Decision Engine refuses to recommend rather than invent."
            ),
            "boundary": (
                "Do not commit to a recommendation until at least one "
                "V1 rule matches or more domain rules are authored"
            ),
            "applicability": (
                "Suitable only as a placeholder while the user "
                "supplies missing context"
            ),
            "_trace": {
                "rule_id": None,
                "rule_name": None,
                "signals": {k: bool(v) for k, v in signals.items()},
                "all_matched_rules": [],
            },
            "_engine_version": "decision_engine_v1",
            "_matched_signals": {},
        }


# ---------------------------------------------------------------------------
# Stage wrapper (Sprint 19.1 wire contract preserved)
# ---------------------------------------------------------------------------

class DecisionModule(Stage):
    """Pipeline stage: `decision`.

    Same Stage contract as the Sprint 19.1 placeholder; the actual
    reasoning moved into `DecisionEngine`.
    """

    name = "decision"

    def __init__(self, engine: DecisionEngine | None = None) -> None:
        self.engine = engine or DecisionEngine()

    def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.decision_object = self.engine.decide(
            project=ctx.project,
            human_context=ctx.human_context,
            knowledge_patterns=ctx.knowledge_patterns,
        )
        return ctx


__all__ = [
    "DecisionEngine",
    "DecisionModule",
    "Rule",
    "RuleR1_LackIdentityWithEquipment",
    "RuleR2_BudgetConflictWithLargeFacility",
    "RuleR3_OverloadedSpace",
]