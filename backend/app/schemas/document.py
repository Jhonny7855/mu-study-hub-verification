"""Pydantic schemas for request/response validation (see section 3 & 4)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response model for a document (read-only)."""

    id: int
    filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    page_count: int
    student_id: int
    student_name: str
    uploaded_at: datetime
    current_status: str

    model_config = {"from_attributes": True}


class VerificationResponse(BaseModel):
    """AI verification output JSON (section 3)."""

    is_academic: bool
    category: str
    confidence: int = Field(ge=0, le=100)
    summary: str
    detected_subject: str | None
    detected_topics: list[str]
    language: str
    quality_status: str
    reason: str
    recommendation: str
    suspicious_flags: list[str] = []
    model_name: str = "heuristic"
    raw_response: str | None = None

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    """Full document details including latest verification."""

    verification: VerificationResponse | None = None


class UploadResponse(BaseModel):
    """Response after a student uploads a document."""

    document_id: int
    filename: str
    file_size: int
    status: str
    message: str


class AIVerifyRequest(BaseModel):
    """Internal request sent to the classification engine."""

    document_id: int
    extracted_text: str
    filename: str
    max_tokens: int = 2048


class AIVerifyResponse(BaseModel):
    """Internal response from the classification engine."""

    is_academic: bool
    category: str
    confidence: int
    summary: str
    detected_subject: str | None
    detected_topics: list[str]
    language: str
    quality_status: str
    suspicious_flags: list[str]
    ai_recommendation: str
    model_name: str
    raw_response: str | None = None


class FileValidationResult(BaseModel):
    """Result of STEP 1 file validation."""

    is_valid: bool
    errors: list[str] = []
    filename: str
    file_size: int
    mime_type: str
    sha256_hash: str | None = None
    actual_pdf: bool = False
    page_count: int = 0
    is_password_protected: bool = False
    is_corrupted: bool = False


class TextExtractionResult(BaseModel):
    """Result of STEP 2 text extraction."""

    success: bool
    text: str = ""
    error: str | None = None
    is_ocr: bool = False
    page_count: int = 0
    metadata: dict[str, Any] = {}


class ClassificationResult(BaseModel):
    """Final classification decision (section 3)."""

    is_academic: bool
    category: str
    confidence: int
    summary: str
    detected_subject: str | None
    detected_topics: list[str]
    language: str
    quality_status: str
    reason: str
    recommendation: str
    suspicious_flags: list[str] = []


class AdminActionRequest(BaseModel):
    """Request when admin takes action on a document."""

    document_id: int
    action: str  # approve, reject, request_manual_review
    admin_id: str
    notes: str | None = None


class AdminActionResponse(BaseModel):
    """Response after admin action."""

    success: bool
    document_id: int
    new_status: str
    message: str