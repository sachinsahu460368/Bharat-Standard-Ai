"""Service for managing the standards relationship graph."""

from __future__ import annotations

import json
import logging
from typing import Optional

import networkx as nx
from app.core.config import settings
from app.services.standards_service import standards_service
from app.schemas.standards import RelatedStandard

logger = logging.getLogger(__name__)

class StandardsGraphService:
    """Service to handle relationships between Standards using a graph."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._loaded = False

    def load(self) -> None:
        """Load relationships from JSON and build the graph."""
        data_path = settings.base_dir / "data" / "relationships" / "relationships.json"

        if not data_path.exists():
            logger.warning("Relationships file not found at %s", data_path)
            self._loaded = True
            return

        with open(data_path, encoding="utf-8") as fh:
            raw = json.load(fh)

        for rel in raw:
            self.graph.add_edge(
                rel["from"],
                rel["to"],
                relationship_type=rel["relationship"]
            )

        self._loaded = True
        logger.info("Built standards graph with %d nodes and %d edges",
                    self.graph.number_of_nodes(), self.graph.number_of_edges())

    def get_related(self, standard_id: str, max_depth: int = 1, top_k: int = 5) -> list[RelatedStandard]:
        """Find related standards using graph traversal."""
        if not self._loaded:
            self.load()

        if standard_id not in self.graph:
            return []

        # Find neighbors within max_depth
        related: list[RelatedStandard] = []

        # Use simple traversal based on networkx
        # For prototype, depth=1
        for neighbor in self.graph.neighbors(standard_id):
            edge_data = self.graph.get_edge_data(standard_id, neighbor)
            std = standards_service.get_by_id(neighbor)

            if std:
                related.append(RelatedStandard(
                    standard_id=neighbor,
                    title=std.title,
                    relationship_type=edge_data["relationship_type"],
                    depth=1
                ))

        return related[:top_k]

# Module-level singleton
standards_graph_service = StandardsGraphService()
