"""Shared test fixtures — ensures services are loaded before tests run."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.compliance_service import compliance_service
from app.services.lexical_search_service import lexical_search_service
from app.services.semantic_search_service import semantic_search_service
from app.services.standards_service import standards_service


def _ensure_services_loaded():
    """Load standards + build BM25 index + FAISS index if not already done.

    The FastAPI lifespan does this when the real server starts, but in
    unit tests that import the singletons directly (not through the
    ASGI client) we need to do it eagerly.
    """
    if not standards_service.is_loaded:
        standards_service.load()
    if not compliance_service.is_loaded:
        compliance_service.load()
    if not lexical_search_service.is_built:
        lexical_search_service.build(standards_service)
    if not semantic_search_service.is_ready:
        semantic_search_service.initialize()
        if not semantic_search_service.has_index:
            semantic_search_service.build_or_refresh_index()


# Run once per test session
_ensure_services_loaded()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """HTTP client that triggers FastAPI lifespan events."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
