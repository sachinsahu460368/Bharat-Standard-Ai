"""Service for detecting QCO/certification compliance for standards."""

from __future__ import annotations
import json
import logging
from typing import Optional, Dict

from app.core.config import settings
from app.schemas.analysis import ComplianceResult

logger = logging.getLogger(__name__)

class ComplianceService:
    """Service to check compliance (QCO) for standards."""

    def __init__(self) -> None:
        self._compliance_data: Dict[str, dict] = {}
        self._loaded = False

    def load(self, path: Optional[str | Path] = None) -> None:
        """Load compliance data from QCO JSON."""
        data_path = Path(path) if path else settings.base_dir / "data" / "compliance" / "qco.json"
        if not data_path.exists():
            logger.warning("Compliance file not found at %s", data_path)
            self._loaded = True
            return

        with open(data_path, encoding="utf-8") as fh:
            raw: list[dict] = json.load(fh)

        for entry in raw:
            # Index by standard_number
            self._compliance_data[entry["standard_number"].upper()] = entry

        self._loaded = True
        logger.info("Loaded %d compliance records from %s", len(self._compliance_data), data_path)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def check_compliance(self, standard_id: str, standard_number: str) -> ComplianceResult:
        """Check compliance for a standard."""

        data = self._compliance_data.get(standard_number.upper().strip())

        if data:
            return ComplianceResult(
                standard_id=standard_id,
                status="APPLICABLE" if data.get("mandatory") else "REQUIRES_VERIFICATION",
                requirement=data.get("certification_type", "N/A"),
                authority=data.get("source", "N/A"),
                evidence=data.get("qco_notification", "N/A"),
                verification_message=data.get("details", "")
            )

        # Default/Not Found
        return ComplianceResult(
            standard_id=standard_id,
            status="NOT_FOUND",
            requirement="N/A",
            authority="N/A",
            evidence="No specific QCO found for this standard.",
            verification_message="Compliance status lookup found no mandatory QCO record."
        )

# Module-level singleton
compliance_service = ComplianceService()
"""
Co-Authored-By: Claude Code <noreply@anthropic.com>
"""
