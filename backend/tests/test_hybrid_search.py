"""Tests for hybrid search service integration."""

import pytest
from httpx import AsyncClient
from app.services.hybrid_search_service import hybrid_search_service

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
    # Should have a mixture of results or at least successful results
    assert "standard_number" in data["results"][0]

def test_hybrid_service_deduplication():
    # Verify the service merges results and doesn't contain duplicates
    results = hybrid_search_service.search("LED", top_k=5)
    ids = [r.standard_id for r in results]
    assert len(ids) == len(set(ids))

@pytest.mark.anyio
async def test_hybrid_search_exact_match_boost(client: AsyncClient):
    # Ensure exact match boost is honored
    resp = await client.post(
        "/api/v1/search",
        json={"query": "IS 10322", "top_k": 3, "search_type": "hybrid"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Exact match for IS 10322 boosted in LEXICAL component,
    # should still dominate hybrid score
    assert "IS 10322" in data["results"][0]["standard_number"]
    assert data["results"][0]["score"] > 0.5
