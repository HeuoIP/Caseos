"""Knowledge Retrieval Schema Constants V1 (Sprint 24.0-A).

This module declares the **structural constants** for the
retrieval contract layer:

    * MATCH_MODE_ALLOW_LIST     -- {"any", "all", "exact"}
    * SORT_BY_ALLOW_LIST        -- {"score", "knowledge_id",
                                    "version", "created_at"}
    * SORT_ORDER_ALLOW_LIST     -- {"asc", "desc"}
    * DEFAULT_QUERY_FIELDS      -- the textual KO fields the
                                   V1 keyword engine scans by
                                   default

The constants are deliberately data-only: they are imported
by the validator, the engine, the report module, and the
test suite. No runtime checks happen here -- ``validator.py``
is the place that enforces them.

Architecture boundary (Sprint 24.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object  (KO schema)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple

# The textual fields the V1 keyword engine scans by default
# when ``query_fields`` is empty. These are subsets of
# ``caseos.knowledge.object.schema.REQUIRED_FIELDS`` that
# typically hold free-form content, plus the asset-list
# fields (joined to a single string for matching).
DEFAULT_QUERY_FIELDS: Tuple[str, ...] = (
    "title",
    "description",
    "category",
    "theme",
    "style",
    "color_system",
    "interaction_type",
    "function_tags",
)

# Match modes the V1 keyword engine understands.
MATCH_MODE_ALLOW_LIST: FrozenSet[str] = frozenset({"any", "all", "exact"})

# Allowed sort-by keys.
SORT_BY_ALLOW_LIST: FrozenSet[str] = frozenset(
    {
        "score",
        "knowledge_id",
        "version",
        "created_at",
    }
)

# Allowed sort orders.
SORT_ORDER_ALLOW_LIST: FrozenSet[str] = frozenset({"asc", "desc"})

# Limit bounds applied by the validator (Q3).
MIN_LIMIT: int = 1
MAX_LIMIT: int = 1000

# Version policy -- the V1 retrieval contract is at version 1.
RETRIEVAL_VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
    "current_version": 1,
}

__all__ = [
    "DEFAULT_QUERY_FIELDS",
    "MATCH_MODE_ALLOW_LIST",
    "SORT_BY_ALLOW_LIST",
    "SORT_ORDER_ALLOW_LIST",
    "MIN_LIMIT",
    "MAX_LIMIT",
    "RETRIEVAL_VERSION_POLICY",
]
