"""Semantic search service for Bharat Standards AI, providing vector-based retrieval."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.schemas.standards import RecommendedStandard
from app.services.standards_service import standards_service

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Service to handle vector embeddings and FAISS searching."""

    def __init__(self) -> None:
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self._standard_ids: list[str] = []
        self._is_ready = False
        self._disabled = settings.render_demo_mode
        if self._disabled:
            logger.info("Semantic search service is disabled (RENDER_DEMO_MODE=true).")

    def initialize(self) -> None:
        """Load model and index if available."""
        if self._disabled:
            logger.info("Semantic search service skipped due to RENDER_DEMO_MODE.")
            return

        # Deferred imports to avoid OOM
        global faiss, SentenceTransformer
        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            logger.error("Failed to import semantic search dependencies: %s", e)
            self._is_ready = False
            return

        try:
            logger.info("Initializing semantic search service with model: %s", settings.embedding_model)
            self.model = SentenceTransformer(settings.embedding_model)

            index_path = settings.base_dir / settings.vector_index_path
            ids_path = index_path.with_suffix(".ids.json")

            if index_path.exists() and ids_path.exists():
                self.index = faiss.read_index(str(index_path))
                with open(ids_path, "r", encoding="utf-8") as f:
                    self._standard_ids = json.load(f)
                logger.info("Semantic index loaded with %d standards.", len(self._standard_ids))
            else:
                logger.warning("FAISS index files not found at %s. Semantic search is unavailable until index is built.", index_path)

            self._is_ready = True
        except Exception as e:
            logger.error("Failed to initialize semantic search service: %s", e)
            self._is_ready = False

    def build_or_refresh_index(self) -> None:
        """Create or update embeddings and FAISS index."""
        if not self.model:
            raise RuntimeError("SentenceTransformer model not initialized.")

        global faiss
        import faiss

        all_standards = standards_service.get_all()
        if not all_standards:
            logger.warning("No standards to index.")
            return

        texts = [standards_service.get_searchable_text(s) for s in all_standards]
        self._standard_ids = [s.id for s in all_standards]

        logger.info("Generating embeddings for %d standards...", len(all_standards))
        embeddings = self.model.encode(texts, show_progress_bar=True)
        # Convert to float32 as required by FAISS
        embeddings = embeddings.astype('float32')

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        index_path = settings.base_dir / settings.vector_index_path
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_path))

        ids_path = index_path.with_suffix(".ids.json")
        with open(ids_path, "w", encoding="utf-8") as f:
            json.dump(self._standard_ids, f)

        logger.info("Semantic index built and saved to %s", index_path)

    def search(self, query: str, top_k: int = 5) -> list[RecommendedStandard]:
        """Perform semantic search."""
        if not self.index or not self.model or not self._is_ready:
            logger.warning("Semantic search requested but service not ready.")
            return []

        # Encode query
        embedding = self.model.encode([query]).astype('float32')

        # Search
        distances, indices = self.index.search(embedding, top_k)

        results: list[RecommendedStandard] = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(self._standard_ids):
                continue

            std_id = self._standard_ids[idx]
            std = standards_service.get_by_id(std_id)
            if std:
                # Score conversion (L2 distance to similarity - crude)
                dist = distances[0][i]
                # Assuming approximate normalized scores based on distance
                score = max(0.0, 1.0 - (dist / 10.0))  # Normalize L2

                results.append(
                    RecommendedStandard(
                        standard_id=std.id,
                        standard_number=std.standard_number,
                        title=std.title,
                        relevance="High" if score > 0.5 else "Medium",
                        score=float(round(score, 4)),
                        reason="Semantically related to query."
                    )
                )
        return results

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def has_index(self) -> bool:
        return self.index is not None

# Module-level singleton
semantic_search_service = SemanticSearchService()
