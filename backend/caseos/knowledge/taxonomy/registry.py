"""Knowledge Taxonomy Registry V1 (Sprint 23.1-C).

The ``TaxonomyRegistry`` is the **append-only container**
for ``Taxonomy`` and ``TaxonomyNode`` records. It is the
storage layer that a future Sprint's Retrieval / Evolution
runtime may read from.

Append-only contract (Sprint 23.1-C spec):

    Allowed methods:
        * append_taxonomy(taxonomy)
        * append_node(node)
        * get_taxonomy(taxonomy_id)
        * get_node(node_id)
        * nodes_for_taxonomy(taxonomy_id)
        * children_of(parent_node_id)
        * roots()                  -- all root nodes (parent_node_id is None)
        * count_taxonomies()       -- total Taxonomy records
        * count_nodes()            -- total Node records
        * list_taxonomies()        -- copy of all Taxonomy records
        * list_nodes()             -- copy of all Node records
        * taxonomy_ids()           -- distinct taxonomy ids
        * node_ids()               -- distinct node ids

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

Architecture boundary (Sprint 23.1-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.taxonomy (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import Taxonomy, TaxonomyNode


class TaxonomyRegistryError(Exception):
    """Raised when a forbidden operation is attempted on the registry."""


class TaxonomyRegistry:
    """Append-only container for ``Taxonomy`` and
    ``TaxonomyNode`` records.
    """

    def __init__(self) -> None:
        self._taxonomies: List[Taxonomy] = []
        self._nodes: List[TaxonomyNode] = []

    # ---- Allowed operations: taxonomies ----------------------------

    def append_taxonomy(self, taxonomy: Taxonomy) -> Taxonomy:
        if not isinstance(taxonomy, Taxonomy):
            raise TaxonomyRegistryError(
                "taxonomy must be a Taxonomy instance"
            )
        self._taxonomies.append(taxonomy)
        return taxonomy

    def get_taxonomy(self, taxonomy_id: str) -> Optional[Taxonomy]:
        for t in self._taxonomies:
            if t.taxonomy_id == taxonomy_id:
                return t
        return None

    def list_taxonomies(self) -> List[Taxonomy]:
        return list(self._taxonomies)

    def count_taxonomies(self) -> int:
        return len(self._taxonomies)

    def taxonomy_ids(self) -> List[str]:
        seen: List[str] = []
        for t in self._taxonomies:
            if t.taxonomy_id not in seen:
                seen.append(t.taxonomy_id)
        return seen

    # ---- Allowed operations: nodes ---------------------------------

    def append_node(self, node: TaxonomyNode) -> TaxonomyNode:
        if not isinstance(node, TaxonomyNode):
            raise TaxonomyRegistryError(
                "node must be a TaxonomyNode instance"
            )
        self._nodes.append(node)
        return node

    def get_node(self, node_id: str) -> Optional[TaxonomyNode]:
        for n in self._nodes:
            if n.node_id == node_id:
                return n
        return None

    def list_nodes(self) -> List[TaxonomyNode]:
        return list(self._nodes)

    def count_nodes(self) -> int:
        return len(self._nodes)

    def node_ids(self) -> List[str]:
        seen: List[str] = []
        for n in self._nodes:
            if n.node_id not in seen:
                seen.append(n.node_id)
        return seen

    def nodes_for_taxonomy(self, taxonomy_id: str) -> List[TaxonomyNode]:
        """Return all nodes whose ``path`` starts with a node
        declared in ``Taxonomy.root_node_ids`` for the given
        ``taxonomy_id``. V1 uses a simple heuristic: a node
        belongs to a taxonomy when its ``node_type`` matches
        the taxonomy's ``taxonomy_type`` AND at least one of
        its ancestors is registered in the same registry as
        the taxonomy's roots.

        For V1 we use a simpler rule: a node belongs to a
        taxonomy when ``node_id in taxonomy.root_node_ids``
        OR ``node.parent_node_id`` ultimately traces back to
        a root declared in the same taxonomy's root_node_ids.
        """
        tax = self.get_taxonomy(taxonomy_id)
        if tax is None:
            return []
        # Build the set of node_ids that are reachable from
        # the taxonomy's declared roots.
        reachable: set = set(tax.root_node_ids)
        # Iteratively extend until no new nodes are added.
        changed = True
        while changed:
            changed = False
            for n in self._nodes:
                if (
                    isinstance(n, TaxonomyNode)
                    and n.parent_node_id in reachable
                    and n.node_id not in reachable
                ):
                    reachable.add(n.node_id)
                    changed = True
        return [
            n for n in self._nodes
            if isinstance(n, TaxonomyNode) and n.node_id in reachable
        ]

    def children_of(self, parent_node_id: str) -> List[TaxonomyNode]:
        return [
            n for n in self._nodes
            if isinstance(n, TaxonomyNode)
            and n.parent_node_id == parent_node_id
        ]

    def roots(self) -> List[TaxonomyNode]:
        return [
            n for n in self._nodes
            if isinstance(n, TaxonomyNode) and n.parent_node_id is None
        ]

    # ---- Forbidden operations --------------------------------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "TaxonomyRegistry.update is forbidden; registry is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "TaxonomyRegistry.delete is forbidden; registry is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "TaxonomyRegistry.overwrite is forbidden; registry is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "TaxonomyRegistry.clear is forbidden; registry is append-only"
        )


__all__ = [
    "TaxonomyRegistry",
    "TaxonomyRegistryError",
]
