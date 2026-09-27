"""Tests for Compliance service."""

import pytest
from app.services.compliance_service import compliance_service

def test_compliance_not_applicable_no_qco():
    # Since QCO data is empty, it should be NOT_FOUND
    result = compliance_service.check_compliance("IS_10322_P5_S3", "IS 10322 (Part 5/Sec 3)")
    assert result.status == "NOT_FOUND"
"""
Co-Authored-By: Claude Code <noreply@anthropic.com>
"""
