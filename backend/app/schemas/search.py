"""Pydantic schemas for search endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.standards import RecommendedStandard


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)
    search_type: str = Field("lexical", pattern="^(lexical|semantic|hybrid)$")


class SearchResponse(BaseModel):
    query: str
    results: list[RecommendedStandard]
    total_found: int
    search_type: str = "hybrid"  # hybrid, semantic, lexical
