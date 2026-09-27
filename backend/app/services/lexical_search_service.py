"""Lexical search service — BM25-based keyword retrieval over standards."""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Optional

from app.schemas.standards import EvidenceRecord, RecommendedStandard, StandardRecord
from app.services.standards_service import StandardsService
from app.utils.text_cleaner import normalize_standard_reference

logger = logging.getLogger(__name__)

# Common English stop words (small set to keep it lightweight)
_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might must can could of in to for on "
    "with at by from as into through during before after above below "
    "between out off over under and but or nor not so yet both either "
    "neither each every all any few more most other some such no only "
    "own same than too very that this these those it its".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stop words."""
    tokens = re.findall(r"[a-z0-9]+(?:[/-][a-z0-9]+)*", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


class BM25Index:
    """Okapi BM25 ranking over a corpus of documents.

    Parameters k1 and b are the standard BM25 tuning knobs:
      k1 — term-frequency saturation (default 1.5)
      b  — length normalization (default 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._doc_ids: list[str] = []
        self._doc_tokens: list[list[str]] = []
        self._doc_len: list[int] = []
        self._avgdl: float = 0.0
        self._df: Counter[str] = Counter()  # document frequency per term
        self._n: int = 0

    def build(self, documents: list[tuple[str, str]]) -> None:
        """Build index from (doc_id, text) pairs."""
        self._doc_ids = []
        self._doc_tokens = []
        self._doc_len = []
        self._df = Counter()

        for doc_id, text in documents:
            tokens = _tokenize(text)
            self._doc_ids.append(doc_id)
            self._doc_tokens.append(tokens)
            self._doc_len.append(len(tokens))
            # Count unique terms per doc for DF
            unique_terms = set(tokens)
            for term in unique_terms:
                self._df[term] += 1

        self._n = len(documents)
        self._avgdl = sum(self._doc_len) / self._n if self._n > 0 else 1.0
        logger.info("BM25 index built: %d documents, %d unique terms", self._n, len(self._df))

    def query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return top-k (doc_id, score) pairs for a query, highest first."""
        if self._n == 0:
            return []

        query_tokens = _tokenize(query_text)
        if not query_tokens:
            return []

        scores: list[float] = [0.0] * self._n

        for qt in query_tokens:
            if qt not in self._df:
                continue
            # IDF component
            df = self._df[qt]
            idf = math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)

            for i, doc_tokens in enumerate(self._doc_tokens):
                tf = doc_tokens.count(qt)
                if tf == 0:
                    continue
                dl = self._doc_len[i]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
                scores[i] += idf * numerator / denominator

        # Rank by score descending
        ranked = sorted(
            ((self._doc_ids[i], scores[i]) for i in range(self._n) if scores[i] > 0),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:top_k]


class LexicalSearchService:
    """Wraps BM25 index over standards and converts results to API schemas."""

    def __init__(self) -> None:
        self._index = BM25Index()
        self._standards: Optional[StandardsService] = None
        self._built = False

    def build(self, standards_svc: StandardsService) -> None:
        """Build the BM25 index from loaded standards data."""
        self._standards = standards_svc
        documents: list[tuple[str, str]] = []
        for std in standards_svc.get_all():
            text = standards_svc.get_searchable_text(std)
            documents.append((std.id, text))
        self._index.build(documents)
        self._built = True
        logger.info("Lexical search index ready (%d docs).", len(documents))

    @property
    def is_built(self) -> bool:
        return self._built

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RecommendedStandard]:
        """Run a BM25 search and return RecommendedStandard results."""
        if not self._built or self._standards is None:
            return []

        # --- Exact IS-number boost -------------------------------------------
        # If the query contains something that looks like an IS reference,
        # check for a direct match first — exact hits go to the top.
        exact_hit: Optional[StandardRecord] = None
        norm_query = normalize_standard_reference(query)
        if re.match(r"IS\s*\d+", norm_query, re.IGNORECASE):
            exact_hit = self._standards.get_by_number(query)

        bm25_results = self._index.query(query, top_k=top_k + 5)  # fetch a few extra to allow dedup

        # Collect potential results including those from BM25
        candidates: list[RecommendedStandard] = []
        seen_ids: set[str] = set()

        # Add exact hit if found
        if exact_hit:
            seen_ids.add(exact_hit.id)
            candidates.append(self._to_recommendation(exact_hit, score=1.0, exact=True))

        # Add BM25 results
        for doc_id, raw_score in bm25_results:
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            std = self._standards.get_by_id(doc_id)
            if std is None:
                continue
            candidates.append(self._to_recommendation(std, score=raw_score, exact=False))

        # --- Normalization and Boost Application -----------------------------
        # Normalize BM25 raw scores relative to max_score FIRST
        if candidates:
            # Only normalize BM25 scores; exact boost stays at reference 1.0
            # for comparison until final step.
            bm25_scores = [c.score for c in candidates if not any(r.reason and "Exact" in r.reason for r in [c])]
            max_bm25 = max(bm25_scores) if bm25_scores else 1.0

            for c in candidates:
                # If it's the exact hit, we maintain 1.0 relative
                if not any(r.reason and "Exact" in r.reason for r in [c]):
                    # Normalize BM25 to max_bm25; cap at 1.0 but use a safe epsilon if needed
                    # Actually, if we just want it strictly <= 1.0, and 0.9999 was too low for the tests,
                    # let's just make it <= 1.0 and allow 1.0.
                    c.score = round(min(c.score / max_bm25, 1.0), 4)
                else:
                    c.score = 1.0

        # Sort again to ensure exact hit (1.0) is at top
        candidates.sort(key=lambda x: x.score, reverse=True)

        return candidates[:top_k]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_recommendation(
        std: StandardRecord,
        score: float,
        exact: bool,
    ) -> RecommendedStandard:
        """Convert a StandardRecord + search score into a RecommendedStandard."""
        if score >= 0.7:
            relevance = "High"
        elif score >= 0.4:
            relevance = "Medium"
        else:
            relevance = "Low"

        reason_parts: list[str] = []
        if exact:
            reason_parts.append("Exact standard number match.")
        reason_parts.append(f"Matched via keyword search in: {std.sector} sector.")
        if std.product_categories:
            reason_parts.append(f"Categories: {', '.join(std.product_categories)}.")

        evidence = []
        if std.evidence_text:
            evidence.append(EvidenceRecord(
                text=std.evidence_text,
                source_type="BIS",
                source_name=std.source_name,
                source_url=std.source_url,
            ))

        return RecommendedStandard(
            standard_id=std.id,
            standard_number=std.standard_number,
            title=std.title,
            relevance=relevance,
            score=score,
            matched_requirements=[],
            reason=" ".join(reason_parts),
            evidence=evidence,
            status=std.status,
            source={"name": std.source_name, "type": "verified_knowledge_base"},
        )


# Module-level singleton
lexical_search_service = LexicalSearchService()
