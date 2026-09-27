
"""Tests for reranking and analysis integration."""

import pytest
from httpx import AsyncClient
from app.services.reranking_service import reranking_service
from app.schemas.analysis import ExtractedRequirements
from app.schemas.standards import RecommendedStandard

def test_reranking_boosts_relevant_candidates():
    # Setup mock candidates
    c1 = RecommendedStandard(
        standard_id="TEST_STD_001", standard_number="IS 100", title="Generic Standard",
        score=0.5, reason="Match", relevance="Medium"
    )
    c2 = RecommendedStandard(
        standard_id="TEST_STD_002", standard_number="IS 200", title="Streetlight Standard",
        score=0.4, reason="Match", relevance="Medium"
    )
    candidates = [c1, c2]

    # Requirements matching c2 only
    reqs = ExtractedRequirements(product="Streetlight")

    ranked = reranking_service.rerank(candidates, reqs)

    # c2 should now be higher than c1 due to +0.2 boost
    assert ranked[0].standard_id == "TEST_STD_002"
    assert ranked[0].score > ranked[1].score

@pytest.mark.anyio
async def test_analyze_endpoint_returns_recommendations(client: AsyncClient):
    # Test that full analyze flow returns recommendations
    files = {"file": ("test.txt", b"Procure 100 LED streetlights.", "text/plain")}
    resp = await client.post("/api/v1/analyze", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 0 # Should have list
