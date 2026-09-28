"""Knowledge Retrieval Report V1 (Sprint 24.0-A).

Generates the operator-facing Markdown report that
describes a ``RetrievalQuery`` -> ``RetrievalResult``
flow, including validation results, sort/limit settings,
and the top hits.

Sections (Sprint 24.0-A spec):

    # Knowledge Retrieval Report
    ## 1. Query Summary
    ## 2. Validation
    ## 3. Engine Selection
    ## 4. Hits (top N)
    ## 5. Architecture Boundary
    ## 6. Notes

Architecture boundary (Sprint 24.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object  (KO schema)
        * caseos.knowledge.retrieval (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from .object import (
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from .schema import (
    DEFAULT_QUERY_FIELDS,
    MATCH_MODE_ALLOW_LIST,
    MAX_LIMIT,
    MIN_LIMIT,
    SORT_BY_ALLOW_LIST,
    SORT_ORDER_ALLOW_LIST,
)
from .validator import RetrievalValidationResult


def _format_query(query: RetrievalQuery) -> List[str]:
    lines: List[str] = []
    lines.append("- query_id: `" + str(query.query_id) + "`")
    lines.append("- version: " + str(query.version))
    lines.append("- query_text: `" + str(query.query_text) + "`")
    lines.append("- match_mode: `" + str(query.match_mode) + "`")
    lines.append("- limit: " + str(query.limit)
                 + " (allowed "
                 + str(MIN_LIMIT) + ".." + str(MAX_LIMIT) + ")")
    lines.append("- sort_by: `" + str(query.sort_by) + "`")
    lines.append("- sort_order: `" + str(query.sort_order) + "`")
    lines.append("- query_fields: " + repr(list(query.query_fields)))
    lines.append("- filters: " + repr(dict(query.filters)))
    lines.append("- required_attributes: "
                 + repr(list(query.required_attributes)))
    lines.append("- bound_domain_ids: "
                 + repr(list(query.bound_domain_ids)))
    lines.append("- created_at: `" + str(query.created_at) + "`")
    lines.append("- created_by: `" + str(query.created_by) + "`")
    return lines


def _format_validation(v: Optional[RetrievalValidationResult]) -> List[str]:
    lines: List[str] = []
    if v is None:
        lines.append("- (no validation result supplied)")
        return lines
    lines.append("- valid: " + ("True" if v.valid else "False"))
    if v.rule_failures:
        lines.append("- rule_failures: " + ", ".join(v.rule_failures))
    if v.errors:
        for e in v.errors:
            lines.append("  - " + str(e))
    else:
        lines.append("- errors: (none)")
    return lines


def _format_hit(idx: int, h: RetrievalHit) -> List[str]:
    lines: List[str] = []
    lines.append("### Hit " + str(idx + 1))
    lines.append("")
    lines.append("- knowledge_id: `" + str(h.knowledge_id) + "`")
    lines.append("- knowledge_version: "
                 + str(h.knowledge_version))
    lines.append("- match_score: " + format(h.match_score, ".4f"))
    lines.append("- matched_fields: "
                 + repr(list(h.matched_fields)))
    if h.matched_snippets:
        lines.append("- matched_snippets:")
        for k, v in h.matched_snippets.items():
            lines.append("  - `" + str(k) + "`: `" + str(v) + "`")
    return lines


def generate_retrieval_report(
    query: RetrievalQuery,
    result: Optional[RetrievalResult],
    validation: Optional[RetrievalValidationResult] = None,
    engine_name: str = "KeywordRetrievalEngine V1",
    *,
    top_n: int = 10,
) -> str:
    """Return a Markdown representation of a retrieval run.

    Parameters
    ----------
    query:
        The query that was executed.
    result:
        The engine output. ``None`` if the engine was not run.
    validation:
        The validator output. ``None`` to skip section 2.
    engine_name:
        Free-form label for the engine. Defaults to the V1
        keyword engine.
    top_n:
        Maximum number of hits to render in section 4.
    """
    lines: List[str] = []

    # ---- Title --------------------------------------------------
    lines.append("# Knowledge Retrieval Report")
    lines.append("")
    lines.append("Sprint 24.0-A -- Knowledge Retrieval Contract V1")
    lines.append("")

    # ---- 1. Query Summary --------------------------------------
    lines.append("## 1. Query Summary")
    lines.append("")
    lines.extend(_format_query(query))
    lines.append("")

    # ---- 2. Validation ------------------------------------------
    lines.append("## 2. Validation")
    lines.append("")
    lines.extend(_format_validation(validation))
    lines.append("")

    # ---- 3. Engine Selection ------------------------------------
    lines.append("## 3. Engine Selection")
    lines.append("")
    lines.append("- engine: `" + engine_name + "`")
    lines.append("- keyword: pure-deterministic, no LLM, no embedding")
    lines.append("- match_mode allow-list: "
                 + ", ".join(sorted(MATCH_MODE_ALLOW_LIST)))
    lines.append("- sort_by allow-list: "
                 + ", ".join(sorted(SORT_BY_ALLOW_LIST)))
    lines.append("- sort_order allow-list: "
                 + ", ".join(sorted(SORT_ORDER_ALLOW_LIST)))
    lines.append("- default_query_fields: "
                 + ", ".join(DEFAULT_QUERY_FIELDS))
    lines.append("")

    # ---- 4. Hits -------------------------------------------------
    lines.append("## 4. Hits (top " + str(max(0, top_n)) + ")")
    lines.append("")
    if result is None:
        lines.append("(no result -- engine was not executed)")
        lines.append("")
    elif not result.success:
        lines.append("- engine did not run successfully")
        lines.append("- execution_time_ms: "
                     + format(result.execution_time_ms, ".3f"))
        lines.append("")
    else:
        lines.append("- success: True")
        lines.append("- total_hits: " + str(result.total_hits))
        lines.append("- execution_time_ms: "
                     + format(result.execution_time_ms, ".3f"))
        lines.append("- query_id: `" + str(result.query_id) + "`")
        lines.append("- created_at: `" + str(result.created_at) + "`")
        lines.append("")
        if result.total_hits == 0:
            lines.append("(no hits matched the query)")
            lines.append("")
        else:
            for idx, h in enumerate(result.hits[: max(0, top_n)]):
                lines.extend(_format_hit(idx, h))
                lines.append("")

    # ---- 5. Architecture Boundary -------------------------------
    lines.append("## 5. Architecture Boundary")
    lines.append("")
    lines.append("Retrieval layer is **read-only** with respect to:")
    lines.append("- Knowledge Objects (snapshots are deep-copied)")
    lines.append("- Decision Engine, Trust Engine, Recommendation Engine")
    lines.append("- Pipeline wiring")
    lines.append("- Evolution layer")
    lines.append("")
    lines.append("Retrieval layer does NOT introduce:")
    lines.append("- LLM / completion models")
    lines.append("- Embedding models")
    lines.append("- Vector databases")
    lines.append("- Automatic learning")
    lines.append("")

    # ---- 6. Notes -----------------------------------------------
    lines.append("## 6. Notes")
    lines.append("")
    lines.append("- V1 is a pure keyword matcher: deterministic and "
                 "testable.")
    lines.append("- Future engines (SemanticRetrievalEngine, Hybrid) "
                 "must implement `KnowledgeRetrievalEngine`.")
    lines.append("- All I/O objects are "
                 "`@dataclass(frozen=True)` with defensive "
                 "deep-copy of collections.")
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_retrieval_report"]
