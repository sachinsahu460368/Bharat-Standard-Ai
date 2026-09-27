"""Pydantic schemas for standards data."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CertificationInfo(BaseModel):
    certification_type: Optional[str] = None
    mandatory: Optional[bool] = None
    details: Optional[str] = None


class RelatedStandard(BaseModel):
    standard_id: str
    title: str
    relationship_type: str
    depth: int = 1


class StandardRecord(BaseModel):
    id: str
    standard_number: str
    title: str
    scope: str = ""
    sector: str = ""
    product_categories: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    status: str = "Current"  # Current, Superseded, Withdrawn
    publication_year: Optional[int] = None
    revision_year: Optional[int] = None
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: list[str] = Field(default_factory=list)
    amendments: list[str] = Field(default_factory=list)
    source_name: str = "BIS"
    source_url: Optional[str] = None
    evidence_text: str = ""
    certification_info: Optional[CertificationInfo] = None


class StandardDetailResponse(BaseModel):
    standard: StandardRecord
    source: str = "verified_knowledge_base"


class EvidenceRecord(BaseModel):
    text: str
    source_type: str = "BIS"
    source_name: str = "BIS"
    source_url: Optional[str] = None
    page: Optional[int] = None


class RecommendedStandard(BaseModel):
    standard_id: str
    standard_number: str
    title: str
    relevance: str  # High, Medium, Low
    score: float
    matched_requirements: list[str] = Field(default_factory=list)
    reason: str = ""
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    status: str = "Current"
    source: dict = Field(default_factory=lambda: {"name": "BIS", "type": "verified_knowledge_base"})
