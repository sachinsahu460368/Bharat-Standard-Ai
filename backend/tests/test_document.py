"""Tests for document extraction service."""

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.services.document_service import document_service


SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_documents"


# ── Unit tests for DocumentService ──────────────────────────────────


def test_extract_from_text():
    result = document_service.extract_from_text(
        "Procurement of 500 LED luminaires conforming to IS 10322."
    )
    assert result.document.extraction_method == "plaintext"
    assert result.document.content_length > 0
    assert "LED" in result.full_text


def test_extract_txt_file():
    sample = SAMPLE_DIR / "led_streetlight_procurement.txt"
    if not sample.exists():
        pytest.skip("Sample TXT not found")
    data = sample.read_bytes()
    result = document_service.extract(data, "led_streetlight_procurement.txt")
    assert result.document.extraction_method == "plaintext"
    assert "LED" in result.full_text
    assert "IS 10322" in result.full_text


def test_extract_empty_content():
    result = document_service.extract_from_text("Short but valid text content.")
    assert result.full_text == "Short but valid text content."


# ── API-level tests ─────────────────────────────────────────────────


@pytest.mark.anyio
async def test_analyze_with_txt_upload(client: AsyncClient):
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
    assert data["status"] == "completed"
    assert data["document"]["extraction_method"] == "plaintext"
    assert data["document"]["content_length"] > 0
    assert "analysis_id" in data
    assert "timing" in data
    assert data["timing"]["extraction_ms"] >= 0


@pytest.mark.anyio
async def test_analyze_rejects_unsupported_file(client: AsyncClient):
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert resp.status_code == 415
    data = resp.json()
    assert data["error"]["code"] == "INVALID_FILE"


@pytest.mark.anyio
async def test_analyze_rejects_empty_file(client: AsyncClient):
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "EMPTY_FILE"


@pytest.mark.anyio
async def test_analyze_returns_timing(client: AsyncClient):
    content = b"Simple procurement text for timing test."
    resp = await client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    timing = resp.json()["timing"]
    assert "extraction_ms" in timing
    assert "total_ms" in timing
