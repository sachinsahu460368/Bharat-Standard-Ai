"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.services.lexical_search_service import lexical_search_service
from app.services.semantic_search_service import semantic_search_service
from app.services.standards_service import standards_service

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return application health status."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.app_env,
        "standards_loaded": standards_service.is_loaded,
        "standards_count": standards_service.count,
        "lexical_index_built": lexical_search_service.is_built,
        "model_loaded": semantic_search_service.is_ready,  # Updated once embedding model loads (Phase 4)
        "vector_index_loaded": semantic_search_service.has_index,  # Updated once FAISS index loads (Phase 4)
    }
