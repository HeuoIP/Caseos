"""Feedback Contradiction Analyzer Core V1 (Sprint 22.2-B.2).

Sits between a feedback payload and a Knowledge Object. Given a
``feedback`` (anything carrying a ``content`` field or text) and a
Knowledge Object dict, it returns a :class:`ContradictionResult`
saying whether the feedback appears to oppose a known field of the
KO.

Detection is **deterministic keyword matching only**. No LLM, no
embedding, no NLP model, no vector search.

Architecture boundary (Sprint 22.2-B.2 spec section 6):

    Allowed imports:
        * dataclasses
        * typing
        * caseos.knowledge.feedback.evaluation.contradiction

    Forbidden imports:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval

The analyzer is a pure function of its inputs. It does NOT mutate
the Knowledge Object, the Decision rules, the Trust model, or the
feedback store. It does NOT modify the pipeline.

Safety rule (Sprint 22.2-B.2 spec section 5):

    False positive is worse than missing conflict.
    When uncertain -> no conflict.

The matcher therefore requires two simultaneous cues before it
fires: a directive negation on the KO side and a violation phrase
on the feedback side. Single-cue matches are ignored.

Contradiction taxonomy (Sprint 22.2-B.2 spec section 4):

    boundary_conflict     feedback opposes a KO boundary item
    principle_conflict    feedback reverses a KO principle order
    None                  no clear contradiction detected
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Union

from .contradiction import ContradictionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NEGATION_PREFIXES = (
    "do not", "don't", "must not", "mustn't", "should not", "shouldn't",
    "shall not", "shalln't", "never", "no", "avoid", "without", "stop",
)

_ORDER_BEFORE = re.compile(
    r"^\s*(?P<a>[a-z][\w\s\-]{1,40}?)\s+before\s+(?P<b>[a-z][\w\s\-]{1,40}?)\s*\.?\s*$",
    re.IGNORECASE,
)
_ORDER_AFTER = re.compile(
    r"^\s*(?P<a>[a-z][\w\s\-]{1,40}?)\s+after\s+(?P<b>[a-z][\w\s\-]{1,40}?)\s*\.?\s*$",
    re.IGNORECASE,
)

# Directive verbs on the feedback side that make a violation phrase
# credible. Without at least one of these in the feedback, the
# boundary rule is silent (false-positive guard).
_DIRECTIVE_VERBS = (
    "add", "added", "adding", "apply", "applied", "applying",
    "build", "built", "building",
    "create", "created", "creating",
    "do", "does", "doing",
    "place", "placed", "placing",
    "put", "puts", "putting",
    "set", "sets", "setting",
    "use", "used", "using", "utilise", "utilized",
    "make", "makes", "making",
    "give", "gives", "giving",
    "should", "must", "need", "needs", "needs to",
    "recommend", "recommends", "recommended",
    "encourage", "encourages", "encouraged",
)

_WORD = re.compile(r"[a-z][a-z'-]+")


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes, str)):
        return " ".join(str(v) for v in value)
    return str(value)


def _ko_field(ko: Any, path: str) -> Any:
    if not isinstance(ko, dict):
        return None
    cur: Any = ko
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _feedback_content(feedback: Any) -> str:
    """Extract a feedback text payload.

    Accepts:
        * ``FeedbackObject`` (uses ``.content``)
        * ``FeedbackEvent``  (uses ``snapshot['content']`` or ``.note``)
        * ``dict``           (uses ``content`` / ``text`` key)
        * anything else      (falls back to ``str(feedback)``)
    """
    if feedback is None:
        return ""
    content = getattr(feedback, "content", None)
    if isinstance(content, str) and content:
        return content
    snapshot = getattr(feedback, "snapshot", None)
    if isinstance(snapshot, dict):
        c = snapshot.get("content") or snapshot.get("text")
        if isinstance(c, str):
            return c
    note = getattr(feedback, "note", None)
    if isinstance(note, str) and note:
        return note
    if isinstance(feedback, dict):
        c = feedback.get("content") or feedback.get("text")
        if isinstance(c, str):
            return c
    return str(feedback)


def _feedback_id(feedback: Any) -> str:
    for attr in ("id", "feedback_id"):
        v = getattr(feedback, attr, None)
        if isinstance(v, str) and v:
            return v
    if isinstance(feedback, dict):
        for k in ("id", "feedback_id"):
            v = feedback.get(k)
            if isinstance(v, str) and v:
                return v
        snap = feedback.get("snapshot")
        if isinstance(snap, dict):
            for k in ("id", "feedback_id"):
                v = snap.get(k)
                if isinstance(v, str) and v:
                    return v
    return ""


def _target_identity(ko: Any) -> str:
    if isinstance(ko, dict):
        v = ko.get("identity")
        if isinstance(v, str):
            return v
    return ""


def _strip_negation(statement: str) -> Optional[str]:
    """Return the directive with its leading negation removed, or
    ``None`` if no recognised negation prefix is present."""
    text = (statement or "").strip().rstrip(".").strip()
    lower = text.lower()
    for prefix in _NEGATION_PREFIXES:
        if lower.startswith(prefix + " "):
            rest = text[len(prefix):].lstrip()
            return rest or None
    return None


def _has_directive_verb(content: str) -> bool:
    words = set(_WORD.findall(content.lower()))
    return any(verb in words for verb in _DIRECTIVE_VERBS)


def _phrase_present(phrase: str, content: str) -> bool:
    """Return True when the phrase appears as a word-bounded span."""
    if not phrase:
        return False
    pattern = r"\b" + re.escape(phrase.lower()) + r"\b"
    return re.search(pattern, content.lower()) is not None


def _boundary_items(ko: Any) -> list[str]:
    raw = _ko_field(ko, "boundary")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Iterable):
        return [str(x) for x in raw if isinstance(x, (str, int, float))]
    return []


def _check_boundary(boundary_items: list[str], content: str) -> Optional[str]:
    """Return the matched boundary item if a contradiction fires."""
    if not boundary_items or not _has_directive_verb(content):
        return None
    for item in boundary_items:
        violation = _strip_negation(item)
        if not violation:
            continue
        if _phrase_present(violation, content):
            return item
    return None


# Leading verbs stripped from "X" and "Y" of "<X> before <Y>".
# Order matters: longer phrases first to avoid greedy partial match.
_LEADING_VERBS: tuple[str, ...] = (
    "creating", "created", "create",
    "building", "built", "build",
    "establishing", "established", "establish",
    "designing", "designed", "design",
    "developing", "developed", "develop",
    "forming", "formed", "form",
    "adding", "added", "add",
    "applying", "applied", "apply",
    "placing", "placed", "place",
    "making", "made", "make",
    "introducing", "introduced", "introduce",
    "setting", "set",
)


def _strip_leading_verb(phrase: str) -> str:
    """Drop a recognised leading directive verb from ``phrase``.

    "create hierarchy"      -> "hierarchy"
    "adding facilities"     -> "facilities"
    "hierarchy"             -> "hierarchy"
    "play and learn"        -> "play and learn"   (no verb matched)

    Conservative: if the first word is not in the verb list, the
    phrase is returned unchanged. This avoids accidental stripping
    of nouns that happen to start with a verb-shaped word.
    """
    text = (phrase or "").strip()
    if not text:
        return text
    parts = text.split(None, 1)
    head = parts[0].lower().rstrip(",.;:")
    for verb in _LEADING_VERBS:
        if head == verb:
            return parts[1].strip() if len(parts) > 1 else text
    return text


def _noun_phrase(phrase: str) -> str:
    """Return the noun phrase X (or Y) used in the reversal test.

    For "Create hierarchy before adding facilities" the regex
    captures ``a="create hierarchy"`` and ``b="adding facilities"``;
    this helper turns them into ``X="hierarchy"`` and
    ``Y="facilities"`` per Sprint 22.2-B.2.1 specification.
    """
    stripped = _strip_leading_verb(phrase)
    return stripped.strip().lower() or phrase.strip().lower()


def _check_principle(principle: str, content: str) -> bool:
    """Return True when feedback reverses a '<X> before <Y>' ordering.

    Per Sprint 22.2-B.2.1:

      * Pattern matched: ``<X> before <Y>``.
      * X and Y are extracted as the noun phrases (a leading
        directive verb is dropped: "create hierarchy" -> X =
        "hierarchy", "adding facilities" -> Y = "facilities").
      * A conflict fires only when the feedback mentions Y AND
        uses an explicit reversal cue against X ("without X" /
        "instead of X"). Single-cue matches are ignored (false-
        positive guard).
      * Symmetric handling for the less common "<X> after <Y>"
        form: a conflict fires only when the feedback mentions X
        AND skips Y.
      * When uncertain, the function returns False. False positive
        is worse than missing conflict.
    """
    text = (principle or "").strip()
    if not text:
        return False
    content_lc = content.lower()
    m = _ORDER_BEFORE.match(text)
    if m:
        x = _noun_phrase(m.group("a"))
        y = _noun_phrase(m.group("b"))
        y_present = _phrase_present(y, content)
        reversal = re.search(
            r"\bwithout\b\s+" + re.escape(x), content_lc
        ) or re.search(
            r"\binstead of\b\s+" + re.escape(x), content_lc
        )
        return bool(y_present and reversal)
    m = _ORDER_AFTER.match(text)
    if m:
        x = _noun_phrase(m.group("a"))
        y = _noun_phrase(m.group("b"))
        # "<X> after <Y>" -- a reversal would skip Y.
        return bool(_phrase_present(x, content) and not _phrase_present(y, content))
    return False


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContradictionAnalyzer:
    """Deterministic contradiction detector.

    Stateless. ``analyze`` is a pure function of
    ``(feedback, knowledge_object)``.
    """

    def analyze(
        self,
        feedback: Any,
        knowledge_object: Any,
    ) -> ContradictionResult:
        content = _feedback_content(feedback)
        feedback_id = _feedback_id(feedback)
        target_identity = _target_identity(knowledge_object)

        # Rule 1: boundary conflict ----------------------------------
        boundary_items = _boundary_items(knowledge_object)
        boundary_match = _check_boundary(boundary_items, content)
        if boundary_match:
            return ContradictionResult(
                feedback_id=feedback_id,
                target_identity=target_identity,
                has_conflict=True,
                conflict_type="boundary_conflict",
                matched_field="boundary",
                explanation=(
                    "feedback content appears to violate a directive on "
                    "the Knowledge Object's 'boundary' field "
                    f"(matched: {boundary_match!r})."
                ),
                requires_human_review=True,
            )

        # Rule 2: principle conflict ---------------------------------
        principle = _as_text(_ko_field(knowledge_object, "principle"))
        if principle and _check_principle(principle, content):
            return ContradictionResult(
                feedback_id=feedback_id,
                target_identity=target_identity,
                has_conflict=True,
                conflict_type="principle_conflict",
                matched_field="principle",
                explanation=(
                    "feedback content appears to reverse the ordering "
                    f"stated in the Knowledge Object's 'principle' field "
                    f"(matched: {principle!r})."
                ),
                requires_human_review=True,
            )

        # Rule 3: unknown --------------------------------------------
        return ContradictionResult(
            feedback_id=feedback_id,
            target_identity=target_identity,
            has_conflict=False,
            conflict_type=None,
            matched_field="",
            explanation=(
                "no clear contradiction detected between feedback content "
                "and the Knowledge Object's boundary / principle fields."
            ),
            requires_human_review=True,
        )


__all__ = ["ContradictionAnalyzer"]
