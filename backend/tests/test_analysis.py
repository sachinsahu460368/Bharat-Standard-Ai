
"""Tests for analysis endpoints and requirement extraction service."""

import pytest
from httpx import AsyncClient
from app.services.requirement_extraction_service import requirement_extraction_service
from app.schemas.analysis import ExtractedRequirements

def test_extraction_mock_returns_valid_schema():
    # Test service extraction with mock output
    text = "Procure 100 LED streetlights, IS 10322 compliant, 5 years warranty."
    result = requirement_extraction_service.extract(text)
    assert isinstance(result, ExtractedRequirements)

@pytest.mark.anyio
async def test_analyze_endpoint(client: AsyncClient):
    # Test the API endpoint itself
    # Send a simple text file
    files = {"file": ("test.txt", b"Procure 100 LED streetlights. IS 10322.", "text/plain")}
    resp = await client.post("/api/v1/analyze", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "requirements" in data
    assert "analysis_id" in data
    assert data["status"] == "completed"
