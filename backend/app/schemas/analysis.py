"""Pydantic schemas for the /analyze endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ExtractedRequirements(BaseModel):
    product: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[str] = None
    application: Optional[str] = None
    environment: Optional[str] = None
    technical_requirements: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    performance_requirements: list[str] = Field(default_factory=list)
    safety_requirements: list[str] = Field(default_factory=list)
    testing_requirements: list[str] = Field(default_factory=list)
    certification_mentions: list[str] = Field(default_factory=list)
    referenced_standards: list[str] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    filename: str
    pages: int
    content_length: int
    extraction_method: str  # "pymupdf", "docx", "plaintext", "ocr"


class PageText(BaseModel):
    page: int
    text: str


class ExtractionResult(BaseModel):
    document: DocumentInfo
    pages: list[PageText]
    full_text: str


class AnalysisTimingInfo(BaseModel):
    extraction_ms: float = 0
    retrieval_ms: float = 0
    llm_ms: float = 0
    total_ms: float = 0


class AnalysisRequest(BaseModel):
    text: Optional[str] = Field(None, min_length=10, max_length=100_000)


class VersionAlert(BaseModel):
    standard_id: str
    detected_version: Optional[str] = None
    latest_known_version: Optional[str] = None
    status: str  # e.g., "Current", "Superseded", "Unknown"
    message: str
    source: str = "BIS"


class ComplianceResult(BaseModel):
    standard_id: str
    status: str  # APPLICABLE, NOT_APPLICABLE, NOT_FOUND, REQUIRES_VERIFICATION
    requirement: str
    authority: str
    evidence: str
    verification_message: str


class StandardExplanation(BaseModel):
    standard_id: str
    explanation: str
    confidence: str


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str = "completed"
    document: DocumentInfo
    requirements: ExtractedRequirements
    recommendations: list = Field(default_factory=list)
    related_standards: dict = Field(default_factory=dict)
    version_alerts: list[VersionAlert] = Field(default_factory=list)
    compliance: list[ComplianceResult] = Field(default_factory=list)
    explanation: Optional[StandardExplanation] = None
    warnings: list[str] = Field(default_factory=list)
    timing: AnalysisTimingInfo = Field(default_factory=AnalysisTimingInfo)
