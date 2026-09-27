"""Analyze endpoint — document upload → extraction → recommendations."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.core.exceptions import EmptyFileError
from app.core.logging import TimingContext
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisTimingInfo,
    ExtractedRequirements,
)
from app.services.document_service import document_service
from app.services.hybrid_search_service import hybrid_search_service
from app.services.requirement_extraction_service import requirement_extraction_service
from app.services.reranking_service import reranking_service
from app.services.standards_graph_service import standards_graph_service
from app.services.standards_service import standards_service
from app.services.version_service import version_service
from app.services.compliance_service import compliance_service
from app.services.explanation_service import explanation_service
from app.services.report_service import report_service
from app.utils.file_validator import validate_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
) -> AnalysisResponse:
    """Accept a procurement document and return analysis results.

    Currently implements Phase 1-2: file validation + text extraction.
    Later phases will add requirement extraction, retrieval, and recommendations.
    """
    # Read the file content
    content = await file.read()

    if not content:
        raise EmptyFileError()

    # Validate
    safe_name = validate_file(
        filename=file.filename or "unnamed",
        content_type=file.content_type,
        size=len(content),
    )

    # Extract text
    with TimingContext() as extraction_timer:
        result = document_service.extract(content, safe_name)

    # Extract requirements
    with TimingContext() as llm_timer:
        requirements = requirement_extraction_service.extract(result.full_text)

    # Retrieval & Reranking
    query = requirements.product or "standards"
    candidates = hybrid_search_service.search(query, top_k=10)
    recommendations = reranking_service.rerank(candidates, requirements)

    # Enrich with related standards for top recommendation
    related_found = {}
    version_alerts = []
    compliance = []
    explanation = None
    if recommendations:
        top_cand = recommendations[0]
        # Related
        related = standards_graph_service.get_related(top_cand.standard_id)
        if related:
            related_found = {top_cand.standard_id: [r.model_dump() for r in related]}

        # Versioning, Compliance, Explanation
        std_record = standards_service.get_by_id(top_cand.standard_id)
        if std_record:
            # Versioning
            alert = version_service.check_version(std_record)
            if alert:
                version_alerts.append(alert)

            # Compliance
            comp = compliance_service.check_compliance(std_record.id, std_record.standard_number)
            compliance.append(comp)

            # Explanation
            all_reqs = requirements.technical_requirements + requirements.performance_requirements
            explanation = explanation_service.generate_explanation(std_record, all_reqs, version_alerts, compliance)

    analysis_id = uuid4().hex[:16]

    logger.info(
        "Extraction done: file=%s pages=%d chars=%d method=%s time=%.1fms",
        safe_name,
        result.document.pages,
        result.document.content_length,
        result.document.extraction_method,
        extraction_timer.elapsed_ms,
    )

    timing = AnalysisTimingInfo(
        extraction_ms=extraction_timer.elapsed_ms,
        llm_ms=llm_timer.elapsed_ms,
        total_ms=extraction_timer.elapsed_ms + llm_timer.elapsed_ms,
    )

    warnings: list[str] = []
    if result.document.extraction_method == "pymupdf_low_text":
        warnings.append(
            "Very little text extracted from PDF. "
            "The document may be scanned — OCR is not yet configured."
        )

    response = AnalysisResponse(
        analysis_id=analysis_id,
        status="completed",
        document=result.document,
        requirements=requirements,
        recommendations=recommendations,
        related_standards=related_found,
        version_alerts=version_alerts,
        compliance=compliance,
        explanation=explanation,
        warnings=warnings,
        timing=timing,
    )

    # Cache for report generation
    report_service.store(response)

    return response
