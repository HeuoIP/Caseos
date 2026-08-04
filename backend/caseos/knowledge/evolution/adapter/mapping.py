"""Knowledge Object Evolution Mapping Table V1 (Sprint 23.0-B, ADR-020).

The Evolution Runtime (Sprint 22.4.x) and the Interpretation
Policy (Sprint 22.3.2) speak in conceptual terms:

    boundary         (e.g. "Do not add scattered equipment")
    principle        (e.g. "Create hierarchy before adding facilities")
    applicability    (e.g. "Suitable for outdoor sites only")

The Knowledge Object Schema V1 (Sprint 23.0-A) ships with
**19 concrete fields**:

    knowledge_id, version,
    title, description, category,
    project_type, site_type, location_type, space_size,
    theme, style, color_system, interaction_type, function_tags,
    image_refs, document_refs,
    created_at, updated_at, source

Notably, the KO V1 schema does NOT yet declare ``boundary``
or ``principle`` fields. The Evolution Adapter therefore
**maps** each allowed EvolutionChangeType onto the closest
existing KO V1 field. This is the conservative V1 mapping:

    BOUNDARY_UPDATE      -> ``category``
        Categories describe the scope / domain boundary of
        a Knowledge Object ("education", "commercial",
        "residential"). A boundary update is therefore
        modelled as a category reassignment.

    PRINCIPLE_UPDATE     -> ``theme``
        The theme is the closest existing KO field to a
        design principle ("forest", "ocean", "industrial").
        A principle update is therefore modelled as a
        theme reassignment.

    APPLICABILITY_UPDATE -> ``interaction_type``
        Interaction patterns ("exploratory", "guided",
        "free-play") determine how a Knowledge Object
        applies to a site. An applicability update is
        therefore modelled as an interaction_type
        reassignment.

The mapping is **declared** in code so a future Sprint
that adds ``boundary`` / ``principle`` / ``applicability``
fields to the KO schema can override the table without
touching the adapter logic.

Architecture boundary (Sprint 23.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..contracts.change_type import EvolutionChangeType


# ---------------------------------------------------------------------------
# Canonical V1 mapping: EvolutionChangeType -> KnowledgeObject V1 field
# ---------------------------------------------------------------------------

CHANGE_TYPE_TO_KO_FIELD: Dict[EvolutionChangeType, str] = {
    EvolutionChangeType.BOUNDARY_UPDATE: "category",
    EvolutionChangeType.PRINCIPLE_UPDATE: "theme",
    EvolutionChangeType.APPLICABILITY_UPDATE: "interaction_type",
}


V1_MAPPING_NOTE: str = (
    "V1 maps BOUNDARY_UPDATE -> category, PRINCIPLE_UPDATE -> theme, "
    "APPLICABILITY_UPDATE -> interaction_type. The KnowledgeObject V1 "
    "schema does not yet declare boundary / principle / applicability "
    "fields; the adapter maps the conceptual Evolution contract onto "
    "the closest existing KO V1 fields. Override the mapping table at "
    "KnowledgeObjectAdapter construction time when KO V2 ships new fields."
)


def _as_change_type(value: Any) -> Optional[EvolutionChangeType]:
    """Return ``value`` as ``EvolutionChangeType`` or None."""
    if isinstance(value, EvolutionChangeType):
        return value
    if isinstance(value, str):
        try:
            return EvolutionChangeType(value)
        except ValueError:
            return None
    return None


def resolve_target_field(
    change_type: Union[EvolutionChangeType, str, Any],
    mapping_table: Optional[Dict[EvolutionChangeType, str]] = None,
) -> Optional[str]:
    """Return the KO V1 field name for ``change_type``.

    Returns None when ``change_type`` is not in the
    (overridable) ``mapping_table``. The caller is
    responsible for turning None into a rejection.
    """
    ct = _as_change_type(change_type)
    if ct is None:
        return None
    table = mapping_table if mapping_table is not None else CHANGE_TYPE_TO_KO_FIELD
    return table.get(ct, None)


__all__ = [
    "CHANGE_TYPE_TO_KO_FIELD",
    "V1_MAPPING_NOTE",
    "resolve_target_field",
]
