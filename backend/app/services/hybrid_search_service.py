"""Service for hybrid retrieval combining lexical and semantic search."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings
from app.schemas.standards import RecommendedStandard
from app.services.lexical_search_service import lexical_search_service
from app.services.semantic_search_service import semantic_search_service
from app.services.standards_service import standards_service

logger = logging.getLogger(__name__)

class HybridSearchService:
    """Combines lexical and semantic retrieval with metadata boosting."""

    def search(self, query: str, top_k: int = 5) -> list[RecommendedStandard]:
        """Perform hybrid search and merge results."""
        lexical_results = lexical_search_service.search(query, top_k=top_k * 2)
        semantic_results = semantic_search_service.search(query, top_k=top_k * 2)

        # Merge results by ID
        combined: dict[str, RecommendedStandard] = {}

        # Define weight components
        w_lex = settings.hybrid_weight_lexical
        w_sem = settings.hybrid_weight_semantic
        w_meta = settings.hybrid_weight_metadata

        # Map to track scores
        # Note: Lexical results from lexical_service already include the 1.0 exact match boost
        for res in lexical_results:
            combined[res.standard_id] = res
            combined[res.standard_id].score = res.score * w_lex

        for res in semantic_results:
            if res.standard_id in combined:
                combined[res.standard_id].score += res.score * w_sem
            else:
                res.score = res.score * w_sem
                combined[res.standard_id] = res

        # Apply metadata signals (if applicable - placeholders for now, simplified to boost certain sectors)
        for std_id, res in combined.items():
            std = standards_service.get_by_id(std_id)
            meta_score = 0.0
            if std and std.status == "Current":
                meta_score = 1.0

            # Apply metadata boost
            res.score += meta_score * w_meta

        # Convert back to list and sort
        final_results = list(combined.values())
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results[:top_k]

# Module-level singleton
hybrid_search_service = HybridSearchService()
