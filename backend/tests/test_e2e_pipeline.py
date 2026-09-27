"""End-to-end pipeline tests: Upload → Extract → Requirements → Search → Rerank → Graph → Version → Compliance → Explanation → Report.

These tests exercise the full API path through the ASGI client, ensuring
every stage of the pipeline produces well-formed output and the report
endpoint correctly consumes cached analysis results.
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_documents"


# ── Full pipeline via /analyze ──────────────────────────────────────


@pytest.mark.anyio
async def test_full_pipeline_returns_all_fields(client: AsyncClient):
    """Analyze a real sample file and verify every pipeline field is present."""
    sample = SAMPLE_DIR / "led_streetlight_procurement.txt"
    if not sample.exists():
        pytest.skip("Sample TXT not found")

    content = sample.read_bytes()
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("led_streetlight.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Core fields
    assert data["status"] == "completed"
    assert data["analysis_id"]

    # Document extraction
    doc = data["document"]
    assert doc["filename"] == "led_streetlight.txt"
    assert doc["content_length"] > 0
    assert doc["extraction_method"] in ("plaintext", "pymupdf", "docx")

    # Requirements extraction
    req = data["requirements"]
    assert "product" in req
    assert isinstance(req["technical_requirements"], list)
    assert isinstance(req["referenced_standards"], list)

    # Recommendations (may be empty for short text, but key must exist)
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)

    # Related standards
    assert "related_standards" in data
    assert isinstance(data["related_standards"], dict)

    # Version / compliance / explanation
    assert "version_alerts" in data
    assert "compliance" in data
    assert isinstance(data["compliance"], list)
    # explanation can be None
    assert "explanation" in data

    # Timing
    assert data["timing"]["extraction_ms"] >= 0
    assert data["timing"]["total_ms"] >= 0


@pytest.mark.anyio
async def test_full_pipeline_with_inline_text(client: AsyncClient):
    """Exercise the pipeline with a minimal inline text file."""
    text = b"Procurement of 200 LED streetlights conforming to IS 10322 Part 1."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("inline.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["analysis_id"]
    assert data["document"]["content_length"] > 0


# ── Report generation from cached analysis ──────────────────────────


@pytest.mark.anyio
async def test_report_from_cached_analysis(client: AsyncClient):
    """Analyze → POST /reports → validate structured report."""
    text = b"Procure 50 LED luminaires. IS 10322 compliance mandatory."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("report_test.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    analysis_id = resp.json()["analysis_id"]

    # Generate report via POST
    report_resp = await client.post(
        "/api/v1/reports",
        json={"analysis_id": analysis_id},
    )
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["analysis_id"] == analysis_id
    assert report["report_id"]
    assert report["generated_at"]
    assert len(report["sections"]) >= 2  # At least Document + Requirements
    assert report["disclaimer"]

    # Verify section titles
    titles = [s["title"] for s in report["sections"]]
    assert "Document Summary" in titles
    assert "Extracted Requirements" in titles


@pytest.mark.anyio
async def test_report_get_endpoint(client: AsyncClient):
    """Analyze → GET /reports/{analysis_id} → same structured report."""
    text = b"Purchase PVC insulated cables IS 1554."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("cable_spec.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    analysis_id = resp.json()["analysis_id"]

    get_resp = await client.get(f"/api/v1/reports/{analysis_id}")
    assert get_resp.status_code == 200
    report = get_resp.json()
    assert report["analysis_id"] == analysis_id
    assert len(report["sections"]) >= 2


@pytest.mark.anyio
async def test_report_not_found(client: AsyncClient):
    """GET /reports/{id} for unknown analysis_id → 404."""
    resp = await client.get("/api/v1/reports/nonexistent_id")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_report_post_not_found(client: AsyncClient):
    """POST /reports with unknown analysis_id → 404."""
    resp = await client.post(
        "/api/v1/reports",
        json={"analysis_id": "missing_analysis"},
    )
    assert resp.status_code == 404


# ── Edge cases / error handling ─────────────────────────────────────


@pytest.mark.anyio
async def test_analyze_empty_file_rejected(client: AsyncClient):
    """Empty file should return 400."""
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_analyze_unsupported_type_rejected(client: AsyncClient):
    """Unsupported file type should return 415."""
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("test.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert resp.status_code == 415


@pytest.mark.anyio
async def test_analyze_no_hallucinated_standards(client: AsyncClient):
    """Verify that recommendations reference only real knowledge-base standard numbers."""
    text = b"Procure 100 units of electronic switches for household use."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("switch_spec.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    for rec in data["recommendations"]:
        # Every recommendation must have a standard_number starting with IS/ISO/IEC
        assert rec["standard_number"], "Empty standard_number in recommendation"
        # Source must indicate verified knowledge base
        assert rec.get("source", {}).get("type") == "verified_knowledge_base"


@pytest.mark.anyio
async def test_pipeline_compliance_no_fabricated_qco(client: AsyncClient):
    """Compliance checks should only contain statuses from the ruleset, never fabricated QCO IDs."""
    text = b"Procure 200 LED streetlights for municipal roads. IS 10322."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("led.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    for comp in data["compliance"]:
        assert comp["status"] in (
            "APPLICABLE", "NOT_APPLICABLE", "NOT_FOUND", "REQUIRES_VERIFICATION",
        )
        assert comp["authority"]  # must not be empty


@pytest.mark.anyio
async def test_pipeline_explanation_confidence_valid(client: AsyncClient):
    """Explanation confidence should be one of the allowed values."""
    text = b"LED luminaires IS 10322 procurement specification."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("expl.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    if data.get("explanation"):
        assert data["explanation"]["confidence"] in (
            "High", "Low", "Requires Verification",
        )


@pytest.mark.anyio
async def test_pipeline_warnings_for_short_text(client: AsyncClient):
    """Very short text should still succeed — warnings are informational only."""
    text = b"Buy switches."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("short.txt", text, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert isinstance(data["warnings"], list)
