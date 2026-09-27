"""Tests for health endpoint and basic app bootstrap."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_returns_200(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.anyio
async def test_health_contains_expected_fields(client: AsyncClient):
    resp = await client.get("/health")
    data = resp.json()
    expected_keys = {
        "status", "version", "environment",
        "standards_loaded", "standards_count", "lexical_index_built",
        "model_loaded", "vector_index_loaded",
    }
    assert expected_keys.issubset(data.keys())


@pytest.mark.anyio
async def test_health_standards_loaded(client: AsyncClient):
    """After startup, standards should be loaded and BM25 should be built."""
    resp = await client.get("/health")
    data = resp.json()
    assert data["standards_loaded"] is True
    assert data["standards_count"] > 0
    assert data["lexical_index_built"] is True


@pytest.mark.anyio
async def test_docs_available(client: AsyncClient):
    resp = await client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_nonexistent_route_returns_404(client: AsyncClient):
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
