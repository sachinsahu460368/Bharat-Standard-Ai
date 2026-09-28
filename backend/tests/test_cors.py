"""CORS tests for FastAPI backend."""

import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_cors_preflight_production_allowed(client: AsyncClient):
    # Simulate a request from the configured production origin (assuming it matches localhost in default env)
    # The actual production origin via env var isn't set in tests, so we test localhost behavior.
    resp = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"

@pytest.mark.anyio
async def test_cors_preflight_unauthorized_rejected(client: AsyncClient):
    resp = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Depending on FastAPI CORS middleware, it might return 200 OR 403
    # but the crucial part is no Access-Control-Allow-Origin header
    assert "access-control-allow-origin" not in resp.headers
