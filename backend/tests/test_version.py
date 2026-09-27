"""Tests for Version service."""

import pytest
from app.services.version_service import version_service
from app.services.standards_service import standards_service
from app.schemas.standards import StandardRecord

def test_version_current_no_amendments():
    # Load standards to find a generic one
    standards_service.load()
    std = standards_service.get_by_id("IS_10322_P1") # Assuming it's 'Current'
    # Force state for test if needed, or find appropriate standard
    alert = version_service.check_version(std)
    assert alert is None

def test_version_superseded():
    # Need a Superseded standard
    # Constructing a manual test record
    record = StandardRecord(
        id="TEST_SUP",
        standard_number="IS 999",
        title="Old Standard",
        status="Superseded",
        superseded_by=["TEST_NEW"]
    )
    alert = version_service.check_version(record)
    assert alert is not None
    assert alert.status == "Superseded"
    assert "IS 999" in alert.detected_version
