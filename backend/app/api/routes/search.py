"""Search endpoint — hybrid search for standards."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse
from app.services.hybrid_search_service import hybrid_search_service
from app.services.lexical_search_service import lexical_search_service
from app.services.semantic_search_service import semantic_search_service

router = APIRouter(prefix="/api/v1")


@router.post("/search", response_model=SearchResponse)
async def search_standards(request: SearchRequest) -> SearchResponse:
    """Search for standards matching a query."""
    results = []
    if request.search_type == "lexical":
        results = lexical_search_service.search(query=request.query, top_k=request.top_k)
    elif request.search_type == "semantic":
        results = semantic_search_service.search(query=request.query, top_k=request.top_k)
    else:  # hybrid
        results = hybrid_search_service.search(query=request.query, top_k=request.top_k)

    return SearchResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        search_type=request.search_type,
    )
