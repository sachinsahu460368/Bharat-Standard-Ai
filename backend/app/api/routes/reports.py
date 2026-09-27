"""Report generation and retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.reports import ReportRequest, ReportResponse
from app.services.report_service import report_service

router = APIRouter(prefix="/api/v1")


@router.post("/reports", response_model=ReportResponse)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """Generate a structured report from a cached analysis."""
    analysis = report_service.get_analysis(request.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis '{request.analysis_id}' not found.")
    return report_service.generate(analysis)


@router.get("/reports/{analysis_id}", response_model=ReportResponse)
async def get_report(analysis_id: str) -> ReportResponse:
    """Retrieve a report by analysis_id."""
    analysis = report_service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return report_service.generate(analysis)
