"""Knowledge Attribute Registry V1 (Sprint 23.1-D).

The ``AttributeRegistry`` is the **append-only container**
for ``KnowledgeAttribute`` records. It is the storage
layer that a future Sprint's Retrieval / Evolution runtime
may read from.

Append-only contract (Sprint 23.1-D spec):

    Allowed methods:
        * append(attribute)
        * get(attribute_id)
        * for_data_type(data_type)
        * for_attribute_type(attribute_type)
        * required()              -- only required attributes
        * optional()              -- only optional attributes
        * count()
        * list()
        * attribute_ids()

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

Architecture boundary (Sprint 23.1-D spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.attribute (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import KnowledgeAttribute


class AttributeRegistryError(Exception):
    """Raised when a forbidden operation is attempted on the registry."""


class AttributeRegistry:
    """Append-only container for ``KnowledgeAttribute`` records."""

    def __init__(self) -> None:
        self._attributes: List[KnowledgeAttribute] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, attribute: KnowledgeAttribute) -> KnowledgeAttribute:
        if not isinstance(attribute, KnowledgeAttribute):
            raise AttributeRegistryError(
                "attribute must be a KnowledgeAttribute instance"
            )
        self._attributes.append(attribute)
        return attribute

    def get(self, attribute_id: str) -> Optional[KnowledgeAttribute]:
        for a in self._attributes:
            if a.attribute_id == attribute_id:
                return a
        return None

    def list(self) -> List[KnowledgeAttribute]:
        return list(self._attributes)

    def count(self) -> int:
        return len(self._attributes)

    def attribute_ids(self) -> List[str]:
        seen: List[str] = []
        for a in self._attributes:
            if a.attribute_id not in seen:
                seen.append(a.attribute_id)
        return seen

    def for_data_type(self, data_type: str) -> List[KnowledgeAttribute]:
        return [
            a for a in self._attributes if a.data_type == data_type
        ]

    def for_attribute_type(
        self, attribute_type: str,
    ) -> List[KnowledgeAttribute]:
        return [
            a for a in self._attributes
            if a.attribute_type == attribute_type
        ]

    def required(self) -> List[KnowledgeAttribute]:
        return [a for a in self._attributes if bool(a.required)]

    def optional(self) -> List[KnowledgeAttribute]:
        return [a for a in self._attributes if not bool(a.required)]

    # ---- Forbidden operations --------------------------------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AttributeRegistry.update is forbidden; registry is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AttributeRegistry.delete is forbidden; registry is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AttributeRegistry.overwrite is forbidden; registry is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AttributeRegistry.clear is forbidden; registry is append-only"
        )


__all__ = [
    "AttributeRegistry",
    "AttributeRegistryError",
]
