"""Tests for ReportService — structured report generation from analysis data."""

import pytest

from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisTimingInfo,
    ComplianceResult,
    DocumentInfo,
    ExtractedRequirements,
    StandardExplanation,
    VersionAlert,
)
from app.schemas.standards import RecommendedStandard
from app.services.report_service import ReportService


def _make_analysis(**overrides) -> AnalysisResponse:
    """Build a minimal AnalysisResponse, merging *overrides*."""
    defaults = dict(
        analysis_id="rpt_test_001",
        status="completed",
        document=DocumentInfo(
            filename="test.txt", pages=1, content_length=100, extraction_method="plaintext",
        ),
        requirements=ExtractedRequirements(
            product="LED Luminaire",
            technical_requirements=["voltage rated", "IP65"],
            performance_requirements=["50000 hr lifespan"],
            safety_requirements=["IEC 60598"],
            materials=["aluminium"],
            referenced_standards=["IS 10322"],
        ),
        recommendations=[],
        related_standards={},
        version_alerts=[],
        compliance=[],
        explanation=None,
        warnings=[],
        timing=AnalysisTimingInfo(extraction_ms=10, llm_ms=20, total_ms=30),
    )
    defaults.update(overrides)
    return AnalysisResponse(**defaults)


# ── store / get_analysis ────────────────────────────────────────────


def test_store_and_retrieve():
    svc = ReportService()
    analysis = _make_analysis()
    svc.store(analysis)
    retrieved = svc.get_analysis("rpt_test_001")
    assert retrieved is not None
    assert retrieved.analysis_id == "rpt_test_001"


def test_get_analysis_missing():
    svc = ReportService()
    assert svc.get_analysis("nonexistent") is None


# ── generate — section structure ────────────────────────────────────


def test_generate_minimal():
    """Report from a bare analysis should have Document + Requirements sections."""
    svc = ReportService()
    analysis = _make_analysis()
    report = svc.generate(analysis)
    assert report.analysis_id == "rpt_test_001"
    assert report.report_id  # non-empty
    assert report.generated_at  # non-empty

    titles = [s.title for s in report.sections]
    assert "Document Summary" in titles
    assert "Extracted Requirements" in titles
    # No recommendations → placeholder
    assert "Recommended Standards" in titles
    rec_section = next(s for s in report.sections if s.title == "Recommended Standards")
    assert "No standards matched" in rec_section.content


def test_generate_with_recommendations():
    rec = RecommendedStandard(
        standard_id="IS_10322_P5_S3",
        standard_number="IS 10322 (Part 5/Sec 3)",
        title="Luminaires - Part 5: Particular Requirements - Section 3: Luminaires for Road and Street Lighting",
        relevance="High",
        score=0.92,
        matched_requirements=["voltage rated"],
    )
    analysis = _make_analysis(recommendations=[rec])
    report = ReportService().generate(analysis)
    rec_section = next(s for s in report.sections if s.title == "Recommended Standards")
    assert "IS 10322 (Part 5/Sec 3)" in rec_section.content
    assert "0.92" in rec_section.content
    assert "voltage rated" in rec_section.content


def test_generate_with_related_standards():
    related = {"IS_10322_P5_S3": [{"title": "LED Luminaire", "relationship_type": "complements"}]}
    analysis = _make_analysis(related_standards=related)
    report = ReportService().generate(analysis)
    rel_section = next(s for s in report.sections if s.title == "Related Standards")
    assert "LED Luminaire" in rel_section.content
    assert "complements" in rel_section.content


def test_generate_with_version_alerts():
    alert = VersionAlert(
        standard_id="IS_10322_P5_S3",
        detected_version="2017",
        latest_known_version="2017",
        status="Current",
        message="IS 10322 (Part 5/Sec 3):2017 is current",
    )
    analysis = _make_analysis(version_alerts=[alert])
    report = ReportService().generate(analysis)
    alert_section = next(s for s in report.sections if s.title == "Version Alerts")
    assert "Current" in alert_section.content


def test_generate_with_compliance():
    comp = ComplianceResult(
        standard_id="IS_10322_P5_S3",
        status="APPLICABLE",
        requirement="QCO mandatory for LED luminaires",
        authority="BIS",
        evidence="QCO001",
        verification_message="Mandatory certification required.",
    )
    analysis = _make_analysis(compliance=[comp])
    report = ReportService().generate(analysis)
    comp_section = next(s for s in report.sections if s.title == "QCO / Compliance")
    assert "APPLICABLE" in comp_section.content
    assert "BIS" in comp_section.content


def test_generate_with_explanation():
    expl = StandardExplanation(
        standard_id="IS_10322_P5_S3",
        explanation="IS 10322 (Part 5/Sec 3) is recommended because it addresses road and street lighting requirements.",
        confidence="High",
    )
    analysis = _make_analysis(explanation=expl)
    report = ReportService().generate(analysis)
    expl_section = next(s for s in report.sections if s.title == "Expert Explanation")
    assert "road and street lighting" in expl_section.content
    assert "High" in expl_section.content


def test_generate_with_warnings():
    analysis = _make_analysis(warnings=["OCR not configured", "Low text extraction"])
    report = ReportService().generate(analysis)
    warn_section = next(s for s in report.sections if s.title == "Warnings & Verification Notes")
    assert "OCR not configured" in warn_section.content


def test_generate_summary_counts():
    rec = RecommendedStandard(
        standard_id="IS_10322_P5_S3", standard_number="IS 10322 (Part 5/Sec 3)",
        title="Road Lighting", relevance="High", score=0.9,
    )
    comp = ComplianceResult(
        standard_id="IS_10322_P5_S3", status="APPLICABLE",
        requirement="QCO", authority="BIS", evidence="QCO001",
        verification_message="Required.",
    )
    alert = VersionAlert(
        standard_id="IS_10322_P5_S3", status="Current",
        message="Up to date",
    )
    analysis = _make_analysis(
        recommendations=[rec], compliance=[comp], version_alerts=[alert],
    )
    report = ReportService().generate(analysis)
    assert "1 standards recommended" in report.summary
    assert "1 compliance checks" in report.summary
    assert "1 version alerts" in report.summary


def test_report_disclaimer_present():
    analysis = _make_analysis()
    report = ReportService().generate(analysis)
    assert "AI-assisted" in report.disclaimer
    assert "human verification" in report.disclaimer


def test_generate_full_pipeline_sections():
    """A report with all pipeline data should include all 8 section types."""
    rec = RecommendedStandard(
        standard_id="IS_10322_P5_S3", standard_number="IS 10322 (Part 5/Sec 3)",
        title="LED Luminaire", relevance="High", score=0.95,
        matched_requirements=["voltage rated"],
    )
    related = {"IS_10322_P5_S3": [{"title": "LED Driver", "relationship_type": "complements"}]}
    alert = VersionAlert(standard_id="IS_10322_P5_S3", status="Current", message="Up to date")
    comp = ComplianceResult(
        standard_id="IS_10322_P5_S3", status="APPLICABLE",
        requirement="QCO mandatory", authority="BIS",
        evidence="QCO001", verification_message="Required.",
    )
    expl = StandardExplanation(
        standard_id="IS_10322_P5_S3",
        explanation="Addresses LED luminaire safety and performance.",
        confidence="High",
    )
    analysis = _make_analysis(
        recommendations=[rec],
        related_standards=related,
        version_alerts=[alert],
        compliance=[comp],
        explanation=expl,
        warnings=["Test warning"],
    )
    report = ReportService().generate(analysis)
    titles = [s.title for s in report.sections]
    expected = [
        "Document Summary",
        "Extracted Requirements",
        "Recommended Standards",
        "Related Standards",
        "Version Alerts",
        "QCO / Compliance",
        "Expert Explanation",
        "Warnings & Verification Notes",
    ]
    for t in expected:
        assert t in titles, f"Missing section: {t}"
