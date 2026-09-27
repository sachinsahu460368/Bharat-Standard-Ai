"""Tests for search endpoint — lexical (BM25) search (Phase 3)."""

import pytest
from httpx import AsyncClient


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_search_validates_min_query(client: AsyncClient):
    resp = await client.post(
        "/api/v1/search",
        json={"query": "ab"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_search_validates_missing_query(client: AsyncClient):
    resp = await client.post(
        "/api/v1/search",
        json={},
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# Lexical search results
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_search_returns_results_for_led(client: AsyncClient):
    """LED-related query should find LED standards in our knowledge base."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "LED outdoor lighting luminaire", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "LED outdoor lighting luminaire"
    assert data["search_type"] == "lexical"
    assert data["total_found"] > 0

    # At least one result should be an LED standard
    numbers = [r["standard_number"] for r in data["results"]]
    led_numbers = {"IS 10322 (Part 1)", "IS 10322 (Part 5/Sec 3)", "IS 16103 (Part 1)", "IS 16103 (Part 2)"}
    assert any(n in led_numbers for n in numbers), f"Expected an LED standard in {numbers}"


@pytest.mark.anyio
async def test_search_returns_no_results_for_cable(client: AsyncClient):
    """Cable-related query should return no results as we only have LED standards."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "PVC insulated cables power wiring", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] == 0


@pytest.mark.anyio
async def test_search_results_have_required_fields(client: AsyncClient):
    """Each search result should have the fields defined in RecommendedStandard."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "LED luminaire", "top_k": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] > 0

    for result in data["results"]:
        assert "standard_id" in result
        assert "standard_number" in result
        assert "title" in result
        assert "relevance" in result
        assert "score" in result
        assert "reason" in result
        assert "evidence" in result
        assert "status" in result
        assert "source" in result
        assert result["relevance"] in ("High", "Medium", "Low")
        assert 0.0 <= result["score"] <= 1.0


@pytest.mark.anyio
async def test_search_scores_are_normalized(client: AsyncClient):
    """Top result should have score close to 1.0 (normalized)."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "LED luminaire", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    if data["total_found"] > 0:
        assert data["results"][0]["score"] == 1.0


@pytest.mark.anyio
async def test_search_respects_top_k(client: AsyncClient):
    """Should return at most top_k results."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "standard", "top_k": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) <= 2


@pytest.mark.anyio
async def test_search_no_results_for_unrelated_query(client: AsyncClient):
    """A query with no overlap should return zero results."""
    resp = await client.post(
        "/api/v1/search",
        json={"query": "zzzzzyyyxxx completely unrelated", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_found"] == 0
    assert data["results"] == []
