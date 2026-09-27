"""Standards data service — loads, indexes, and queries the standards knowledge base."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.schemas.standards import StandardRecord
from app.utils.text_cleaner import normalize_standard_reference

logger = logging.getLogger(__name__)


class StandardsService:
    """In-memory standards registry loaded from the JSON knowledge base."""

    def __init__(self) -> None:
        self._by_id: dict[str, StandardRecord] = {}
        self._by_number: dict[str, StandardRecord] = {}  # normalized number → record
        self._all: list[StandardRecord] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def load(self, path: Optional[str | Path] = None) -> None:
        """Load standards from JSON file into memory."""
        data_path = Path(path) if path else settings.base_dir / settings.standards_data_path
        if not data_path.exists():
            logger.warning("Standards file not found at %s — starting empty.", data_path)
            self._loaded = True
            return

        with open(data_path, encoding="utf-8") as fh:
            raw: list[dict] = json.load(fh)

        for entry in raw:
            record = StandardRecord(**entry)
            self._by_id[record.id] = record

            # Index by normalized standard number for fast exact-match
            norm = normalize_standard_reference(record.standard_number)
            self._by_number[norm] = record
            # Also index the raw number uppercased
            self._by_number[record.standard_number.upper().strip()] = record

            self._all.append(record)

        self._loaded = True
        logger.info("Loaded %d standards from %s", len(self._all), data_path)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def count(self) -> int:
        return len(self._all)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_by_id(self, standard_id: str) -> Optional[StandardRecord]:
        """Get a standard by its internal ID (e.g. STD001)."""
        return self._by_id.get(standard_id)

    def get_by_number(self, standard_number: str) -> Optional[StandardRecord]:
        """Get a standard by its IS number, with normalized matching."""
        # Try exact first
        upper = standard_number.upper().strip()
        record = self._by_number.get(upper)
        if record:
            return record
        # Try normalized
        norm = normalize_standard_reference(standard_number)
        return self._by_number.get(norm)

    def get_all(self) -> list[StandardRecord]:
        """Return all loaded standards."""
        return list(self._all)

    def filter_by_sector(self, sector: str) -> list[StandardRecord]:
        """Return standards matching a sector (case-insensitive)."""
        sector_lower = sector.lower()
        return [s for s in self._all if s.sector.lower() == sector_lower]

    def filter_by_category(self, category: str) -> list[StandardRecord]:
        """Return standards whose product_categories contain the term."""
        cat_lower = category.lower()
        return [
            s for s in self._all
            if any(cat_lower in c.lower() for c in s.product_categories)
        ]

    def filter_by_status(self, status: str) -> list[StandardRecord]:
        """Return standards matching a status (Current, Superseded, Withdrawn)."""
        status_lower = status.lower()
        return [s for s in self._all if s.status.lower() == status_lower]

    def search_by_keyword(self, keyword: str) -> list[StandardRecord]:
        """Simple keyword containment search across title, scope, keywords."""
        kw_lower = keyword.lower()
        results: list[StandardRecord] = []
        for s in self._all:
            searchable = " ".join([
                s.title,
                s.scope,
                s.standard_number,
                " ".join(s.keywords),
                " ".join(s.product_categories),
                s.evidence_text,
            ]).lower()
            if kw_lower in searchable:
                results.append(s)
        return results

    # ------------------------------------------------------------------
    # Bulk text for indexing (used by lexical & semantic search services)
    # ------------------------------------------------------------------

    def get_searchable_text(self, standard: StandardRecord) -> str:
        """Build a single text block from a standard for search indexing."""
        parts = [
            standard.standard_number,
            standard.title,
            standard.scope,
            " ".join(standard.product_categories),
            " ".join(standard.keywords),
            standard.evidence_text,
            standard.sector,
        ]
        return " ".join(p for p in parts if p)


# Module-level singleton
standards_service = StandardsService()
