"""Service to structure analysis data into a formal report and cache results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.schemas.analysis import AnalysisResponse
from app.schemas.reports import ReportResponse, ReportSection


class ReportService:
    """Service to formulate reports and cache analysis results."""

    def __init__(self) -> None:
        self._cache: dict[str, AnalysisResponse] = {}

    def store(self, analysis: AnalysisResponse) -> None:
        """Cache an analysis result by its analysis_id."""
        self._cache[analysis.analysis_id] = analysis

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResponse]:
        """Retrieve a cached analysis result."""
        return self._cache.get(analysis_id)

    def generate(self, analysis: AnalysisResponse) -> ReportResponse:
        """Formulate a structured report from analysis data."""
        sections: list[ReportSection] = []

        # Section 1: Document
        sections.append(ReportSection(
            title="Document Summary",
            content=(
                f"Filename: {analysis.document.filename}\n"
                f"Pages: {analysis.document.pages}\n"
                f"Characters extracted: {analysis.document.content_length}\n"
                f"Extraction method: {analysis.document.extraction_method}"
            ),
        ))

        # Section 2: Extracted Requirements
        req = analysis.requirements
        req_lines = [f"Product: {req.product or 'N/A'}"]
        if req.technical_requirements:
            req_lines.append(f"Technical requirements: {', '.join(req.technical_requirements)}")
        if req.performance_requirements:
            req_lines.append(f"Performance requirements: {', '.join(req.performance_requirements)}")
        if req.safety_requirements:
            req_lines.append(f"Safety requirements: {', '.join(req.safety_requirements)}")
        if req.materials:
            req_lines.append(f"Materials: {', '.join(req.materials)}")
        if req.referenced_standards:
            req_lines.append(f"Referenced standards: {', '.join(req.referenced_standards)}")
        sections.append(ReportSection(
            title="Extracted Requirements",
            content="\n".join(req_lines),
        ))

        # Section 3: Recommended Standards
        if analysis.recommendations:
            rec_lines = []
            for i, rec in enumerate(analysis.recommendations, 1):
                rec_lines.append(
                    f"{i}. {rec.standard_number} — {rec.title} "
                    f"(Relevance: {rec.relevance}, Score: {rec.score:.2f})"
                )
                if rec.matched_requirements:
                    rec_lines.append(f"   Matched: {', '.join(rec.matched_requirements)}")
            sections.append(ReportSection(
                title="Recommended Standards",
                content="\n".join(rec_lines),
            ))
        else:
            sections.append(ReportSection(
                title="Recommended Standards",
                content="No standards matched the extracted requirements.",
            ))

        # Section 4: Related Standards
        if analysis.related_standards:
            rel_lines = []
            for std_id, rels in analysis.related_standards.items():
                for r in rels:
                    rel_lines.append(f"- {r.get('title', 'N/A')} ({r.get('relationship_type', 'N/A')})")
            sections.append(ReportSection(
                title="Related Standards",
                content="\n".join(rel_lines) if rel_lines else "None found.",
            ))

        # Section 5: Version Alerts
        if analysis.version_alerts:
            alert_lines = [f"- [{a.status}] {a.message}" for a in analysis.version_alerts]
            sections.append(ReportSection(
                title="Version Alerts",
                content="\n".join(alert_lines),
            ))

        # Section 6: Compliance / QCO
        if analysis.compliance:
            comp_lines = [
                f"- {c.standard_id}: {c.status} — {c.requirement} ({c.authority})"
                for c in analysis.compliance
            ]
            sections.append(ReportSection(
                title="QCO / Compliance",
                content="\n".join(comp_lines),
            ))

        # Section 7: Explanation
        if analysis.explanation:
            sections.append(ReportSection(
                title="Expert Explanation",
                content=f"[{analysis.explanation.confidence}] {analysis.explanation.explanation}",
            ))

        # Section 8: Warnings
        if analysis.warnings:
            sections.append(ReportSection(
                title="Warnings & Verification Notes",
                content="\n".join(f"⚠ {w}" for w in analysis.warnings),
            ))

        return ReportResponse(
            report_id=uuid4().hex[:16],
            analysis_id=analysis.analysis_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            sections=sections,
            summary=f"Analysis of '{analysis.document.filename}': "
                     f"{len(analysis.recommendations)} standards recommended, "
                     f"{len(analysis.compliance)} compliance checks, "
                     f"{len(analysis.version_alerts)} version alerts.",
        )


# Module-level singleton
report_service = ReportService()
