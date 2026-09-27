"""Service for detecting standard versions and revision status."""

from __future__ import annotations
from typing import Optional

from app.schemas.analysis import VersionAlert
from app.schemas.standards import StandardRecord
from app.services.standards_service import standards_service

class VersionService:
    """Service to check if a standard is Current, Superseded, or has revisions."""

    def check_version(self, standard: StandardRecord) -> Optional[VersionAlert]:
        """Check the version status of a standard."""

        # 1. Superseded Check
        if standard.status.lower() == "superseded":
            if standard.superseded_by:
                latest_id = standard.superseded_by[0]  # Simplification: assume first is latest/direct
                latest = standards_service.get_by_id(latest_id)
                msg = f"This standard is superseded by {latest.standard_number if latest else latest_id}."
                return VersionAlert(
                    standard_id=standard.id,
                    detected_version=f"{standard.standard_number}",
                    latest_known_version=f"{latest.standard_number if latest else latest_id}",
                    status="Superseded",
                    message=msg
                )
            else:
                return VersionAlert(
                    standard_id=standard.id,
                    status="Superseded",
                    message="This standard is superseded, but no newer version information is available.",
                )

        # 2. Current Check
        if standard.status.lower() == "current":
            if standard.amendments:
                return VersionAlert(
                    standard_id=standard.id,
                    status="Current",
                    message=f"Standard is current but has {len(standard.amendments)} active amendments.",
                )
            return None

        # 3. Default/Unknown
        return VersionAlert(
            standard_id=standard.id,
            status=standard.status,
            message=f"Standard status: {standard.status}. Verification required.",
        )

# Module-level singleton
version_service = VersionService()
