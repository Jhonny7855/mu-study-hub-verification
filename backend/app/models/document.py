"""SQLAlchemy ORM models for documents and verification results."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Enum as SaEnum,
    Float,
    JSON,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all DB models."""

    pass


class DocumentStatus(str, Enum):
    """Document lifecycle states (see section 7 of spec)."""

    UPLOADED = "UPLOADED"
    FILE_VALIDATION = "FILE_VALIDATION"
    AI_ANALYSIS = "AI_ANALYSIS"
    AI_FLAGGED = "AI_FLAGGED"
    PENDING_ADMIN_REVIEW = "PENDING_ADMIN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentCategory(str, Enum):
    """Classified academic document types (section 2, step 3)."""

    ACADEMIC_NOTES = "Academic Notes"
    ASSIGNMENTS = "Assignments"
    WORKSHEETS = "Worksheets"
    RESEARCH_PAPERS = "Research Papers"
    PRACTICAL_FILES = "Practical Files"
    LAB_MANUALS = "Lab Manuals"
    QUESTION_PAPERS = "Question Papers"
    GATE_PREPARATION = "GATE Preparation"
    EDUCATIONAL_BOOKS = "Educational Books"
    PROJECT_REPORTS = "Project Reports"
    TUTORIALS = "Tutorials"
    OTHER_EDUCATIONAL_CONTENT = "Other Educational Content"
    UNRELATED_CONTENT = "Unrelated Content"
    SUSPICIOUS_CONTENT = "Suspicious Content"


class Document(Base):
    """A student-uploaded PDF document."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    page_count: Mapped[int] = mapped_column(default=0)
    is_ocr: Mapped[bool] = mapped_column(default=False)

    # Metadata
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(128), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Status tracking
    current_status: Mapped[DocumentStatus] = mapped_column(
        SaEnum(DocumentStatus), default=DocumentStatus.UPLOADED
    )
    status_updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    verifications: Mapped[list["DocumentAIVerification"]] = relationship(
        "DocumentAIVerification", back_populates="document", cascade="all,delete-orphan"
    )

    # JSONB fields
    duplicate_of_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )

    # Convenience
    def to_dict(self) -> dict[str, Any]:
        """Serialise for JSON responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "sha256_hash": self.sha256_hash,
            "page_count": self.page_count,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "uploaded_at": self.uploaded_at.isoformat(),
            "current_status": self.current_status.value,
        }


class VerificationStatus(str, Enum):
    """Verification result states (section 7)."""

    VERIFIED = "VERIFIED"  # AI completed successfully
    FAILED = "FAILED"  # AI could not process
    MANUAL_REQUIRED = "MANUAL_REQUIRED"  # Unclear, needs human review


class DocumentAIVerification(Base):
    """Immutable AI verification attempt for a document.

    New rows are created on each re-verification, never updated.
    """

    __tablename__ = "document_ai_verifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document: Mapped["Document"] = relationship(
        "Document", back_populates="verifications"
    )

    # AI classification results
    extracted_text_summary: Mapped[str] = mapped_column(Text, nullable=True)
    detected_category: Mapped[str] = mapped_column(String(80), nullable=True)
    detected_subject: Mapped[str] = mapped_column(String(80), nullable=True)
    detected_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_academic: Mapped[bool] = mapped_column(default=False)
    quality_status: Mapped[str] = mapped_column(String=32, default="Unknown")

    # Flags & warnings
    suspicious_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_recommendation: Mapped[str] = mapped_column(String=32, default="PENDING")

    # Audit
    model_name: Mapped[str] = mapped_column(String=64, default="heuristic")
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SaEnum(VerificationStatus), default=VerificationStatus.VERIFIED
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Admin decision (null = not reviewed yet)
    admin_decided: Mapped[bool] = mapped_column(default=False)
    admin_decision_at: Mapped[datetime | None] = mapped_column(nullable=True)
    admin_decision_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Serialise for JSON responses."""
        return {
            "category": self.detected_category,
            "detected_subject": self.detected_subject,
            "detected_topics": self.detected_topics,
            "confidence_score": self.confidence_score,
            "is_academic": self.is_academic,
            "quality_status": self.quality_status,
            "suspicious_flags": self.suspicious_flags,
            "ai_recommendation": self.ai_recommendation,
            "model_name": self.model_name,
            "verification_status": self.verification_status.value,
            "summary": self.extracted_text_summary,
            "admin_reviewed": self.admin_decided,
            "created_at": self.created_at.isoformat(),
        }