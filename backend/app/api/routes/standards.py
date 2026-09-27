"""Standards CRUD endpoint — lookup, detail, related."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.standards_graph_service import standards_graph_service
from app.services.standards_service import standards_service
from app.core.exceptions import StandardNotFoundError

router = APIRouter(prefix="/api/v1")


@router.get("/standards/{standard_id}")
async def get_standard(standard_id: str) -> dict:
    """Return details for a specific standard.

    Accepts an internal ID (e.g. STD001) or an IS number (e.g. IS 10322).
    """
    # Try by internal ID first
    record = standards_service.get_by_id(standard_id)
    if record is None:
        # Try as IS number
        record = standards_service.get_by_number(standard_id)
    if record is None:
        raise StandardNotFoundError(standard_id)
    return record.model_dump()


@router.get("/standards/{standard_id}/related")
async def get_related_standards(standard_id: str, depth: int = 1) -> dict:
    """Return related standards graph."""
    # Validate that the standard exists first
    record = standards_service.get_by_id(standard_id)
    if record is None:
        record = standards_service.get_by_number(standard_id)
    if record is None:
        raise StandardNotFoundError(standard_id)

    related = standards_graph_service.get_related(record.id, max_depth=depth)

    return {
        "standard_id": record.id,
        "standard_number": record.standard_number,
        "related": [r.model_dump() for r in related],
        "depth": depth,
    }


@router.get("/standards/{standard_id}/explanation")
async def get_explanation(standard_id: str) -> dict:
    """Return 'why recommended' explanation for a standard.

    Stub — will be implemented in Phase 7.
    """
    record = standards_service.get_by_id(standard_id)
    if record is None:
        record = standards_service.get_by_number(standard_id)
    if record is None:
        raise StandardNotFoundError(standard_id)

    return {
        "standard_id": record.id,
        "standard_number": record.standard_number,
        "explanation": "Not available in verified knowledge base. Official verification required.",
        "source": "placeholder — LLM explanation will be added in Phase 7",
    }
