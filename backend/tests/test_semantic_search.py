"""Tests for semantic search service."""

import pytest
from httpx import AsyncClient
from app.services.semantic_search_service import semantic_search_service

@pytest.mark.anyio
async def test_semantic_search_service_ready(client: AsyncClient):
    assert semantic_search_service.is_ready is True
    assert semantic_search_service.has_index is True

@pytest.mark.anyio
async def test_semantic_search_query(client: AsyncClient):
    resp = await client.post(
        "/api/v1/search",
        json={"query": "LED outdoor lighting", "top_k": 3, "search_type": "semantic"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["search_type"] == "semantic"
    assert data["total_found"] > 0
    assert "standard_number" in data["results"][0]

@pytest.mark.anyio
async def test_hybrid_search_query(client: AsyncClient):
    resp = await client.post(
        "/api/v1/search",
        json={"query": "LED outdoor lighting", "top_k": 3, "search_type": "hybrid"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["search_type"] == "hybrid"
    assert data["total_found"] > 0
