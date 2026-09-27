"""Tests for standards service and standards endpoint (Phase 3)."""

import pytest
from httpx import AsyncClient

from app.services.standards_service import standards_service


# ------------------------------------------------------------------
# StandardsService unit tests
# ------------------------------------------------------------------

class TestStandardsService:
    """Tests for the in-memory standards registry."""

    def test_service_is_loaded(self):
        assert standards_service.is_loaded is True

    def test_service_has_standards(self):
        assert standards_service.count > 0

    def test_get_by_id(self):
        record = standards_service.get_by_id("IS_10322_P1")
        assert record is not None
        assert "IS 10322" in record.standard_number
        assert "Lighting" in record.title or "luminaires" in record.title.lower()

    def test_get_by_id_not_found(self):
        assert standards_service.get_by_id("NONEXISTENT") is None

    def test_get_by_number_exact(self):
        record = standards_service.get_by_number("IS 10322 (Part 1)")
        assert record is not None
        assert record.id == "IS_10322_P1"

    def test_get_by_number_normalized(self):
        """Lookup with year suffix / different spacing should still match."""
        # This will test the normalization to 'IS 10322'
        record = standards_service.get_by_number("IS 10322")
        assert record is not None
        assert record.id in ["IS_10322_P1", "IS_10322_P5_S3"]

    def test_get_by_number_case_insensitive(self):
        record = standards_service.get_by_number("is 10322 (part 1)")
        assert record is not None
        assert record.id == "IS_10322_P1"

    def test_get_all_returns_list(self):
        all_standards = standards_service.get_all()
        assert isinstance(all_standards, list)
        assert len(all_standards) == standards_service.count

    def test_filter_by_sector(self):
        results = standards_service.filter_by_sector("Electrical")
        assert len(results) > 0
        assert all(r.sector.lower() == "electrical" for r in results)

    def test_filter_by_sector_no_match(self):
        results = standards_service.filter_by_sector("Aerospace")
        assert len(results) == 0

    def test_filter_by_category(self):
        results = standards_service.filter_by_category("LED")
        assert len(results) > 0

    def test_filter_by_status(self):
        current = standards_service.filter_by_status("Current")
        assert len(current) > 0
        assert all(r.status == "Current" for r in current)

    def test_search_by_keyword(self):
        results = standards_service.search_by_keyword("luminaire")
        assert len(results) > 0

    def test_search_by_keyword_no_match(self):
        results = standards_service.search_by_keyword("zzzyyyxxx")
        assert len(results) == 0

    def test_get_searchable_text(self):
        record = standards_service.get_by_id("IS_10322_P1")
        assert record is not None
        text = standards_service.get_searchable_text(record)
        assert "IS 10322" in text
        assert len(text) > 20


# ------------------------------------------------------------------
# Standards endpoint tests
# ------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_standard_by_id(client: AsyncClient):
    resp = await client.get("/api/v1/standards/IS_10322_P1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "IS_10322_P1"
    assert "IS 10322" in data["standard_number"]


@pytest.mark.anyio
async def test_get_standard_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/standards/NONEXISTENT")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_get_standard_has_expected_fields(client: AsyncClient):
    resp = await client.get("/api/v1/standards/IS_10322_P1")
    assert resp.status_code == 200
    data = resp.json()
    required_fields = {
        "id", "standard_number", "title", "scope", "sector",
        "product_categories", "keywords", "status", "source_name",
    }
    assert required_fields.issubset(data.keys())


@pytest.mark.anyio
async def test_get_standard_related(client: AsyncClient):
    """Related endpoint should return empty list for now."""
    resp = await client.get("/api/v1/standards/IS_10322_P1/related")
    assert resp.status_code == 200
    data = resp.json()
    assert data["standard_id"] == "IS_10322_P1"
    assert "related" in data
    assert len(data["related"]) == 0

@pytest.mark.anyio
async def test_get_standard_explanation_stub(client: AsyncClient):
    """Explanation endpoint should return placeholder text."""
    resp = await client.get("/api/v1/standards/IS_10322_P1/explanation")
    assert resp.status_code == 200
    data = resp.json()
    assert "standard_id" in data
    assert "explanation" in data
