"""Pydantic schemas for request/response validation (see section 3 & 4)."""
from .document import (
    AIVerifyRequest,
    AIVerifyResponse,
    AdminActionRequest,
    AdminActionResponse,
    DocumentDetailResponse,
    DocumentResponse,
    FileValidationResult,
    TextExtractionResult,
    UploadResponse,
    ClassificationResult,
)

__all__ = [
    "AIVerifyRequest",
    "AIVerifyResponse",
    "AdminActionRequest",
    "AdminActionResponse",
    "DocumentDetailResponse",
    "DocumentResponse",
    "FileValidationResult",
    "TextExtractionResult",
    "UploadResponse",
    "ClassificationResult",
]