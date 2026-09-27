
"""Service for reranking search candidates based on requirement matches and explanation generation."""

from __future__ import annotations

import logging
from typing import Optional

from app.schemas.analysis import ExtractedRequirements
from app.schemas.standards import EvidenceRecord, RecommendedStandard
from app.services.standards_service import standards_service

logger = logging.getLogger(__name__)

class RerankingService:
    """Reranks search results against extracted procurement requirements."""

    def __init__(self) -> None:
        pass

    def rerank(
        self, candidates: list[RecommendedStandard], requirements: ExtractedRequirements
    ) -> list[RecommendedStandard]:
        """Rerank candidates based on requirement signals."""
        if not candidates:
            return []

        ranked: list[RecommendedStandard] = []
        for cand in candidates:
            # Get full record for metadata analysis
            std = standards_service.get_by_id(cand.standard_id)
            # If std is None, reranking will proceed with limited signals (cand title only)

            # --- Scoring Signals ---
            score_boost = 0.0
            matched_reqs = []

            # 1. Product/Category match (Title + Keywords match)
            if requirements.product:
                product_lower = requirements.product.lower()
                # Check record if available, fallback to candidate title if std record missing
                title_to_check = std.title.lower() if std else cand.title.lower()
                keywords_to_check = [k.lower() for k in std.keywords] if std else []

                if product_lower in title_to_check or product_lower in keywords_to_check:
                    score_boost += 0.3
                    matched_reqs.append(f"Product match: {requirements.product}")

            # 2. Category match
            if requirements.category and std:  # Cat boost requires full record
                cat_lower = requirements.category.lower()
                if cat_lower in [c.lower() for c in std.product_categories]:
                    score_boost += 0.2
                    matched_reqs.append(f"Category match: {requirements.category}")

            # 3. Apply Boost
            cand.score += score_boost

            # --- Update Explanation ---
            cand.matched_requirements = matched_reqs
            if matched_reqs:
                cand.reason = (
                    f"The specification matches {', '.join(matched_reqs)} "
                    "which directly aligns with the standard's scope."
                )
            else:
                cand.reason = (
                    f"General relevance to {cand.title}. "
                    "Specific requirement matches were not definitively identified."
                )

            # --- Populate Evidence ---
            if std and std.evidence_text:
                cand.evidence = [
                    EvidenceRecord(
                        text=std.evidence_text,
                        source_url=std.source_url,
                        source_name=std.source_name
                    )
                ]

            ranked.append(cand)

        # Sort by updated score
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked[:5]

# Module-level singleton
reranking_service = RerankingService()
