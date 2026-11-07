"""Main API routes for the MU STUDY HUB AI Verification Bot.

This module implements the complete verification pipeline:
1. Student uploads PDF
2. File validation
3. Text extraction
4. AI classification
5. Admin review queue
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.config import settings
from app.models.document import Document, DocumentStatus, DocumentAIVerification, VerificationStatus
from app.schemas.document import (
    AdminActionRequest,
    AdminActionResponse,
    DocumentDetailResponse,
    DocumentResponse,
    UploadResponse,
    AIVerifyRequest,
)
from app.services.classifier import classify_document
from app.services.file_validator import validate_upload
from app.services.text_extractor import extract_text

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Simple in-memory admin verification (in production, use proper auth)
_valid_admins: set[str] = set(settings.admin_user_list)


# ============================================================================
# Background task: Run AI verification pipeline
# ============================================================================

async def run_verification_pipeline(
    document_id: int,
    storage_path: str,
    filename: str,
    student_id: int,
    student_name: str,
):
    """Execute the complete verification pipeline in background."""
    from sqlalchemy import select as sql_select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Create engine (in production, use singleton)
    if "sqlite" in settings.database_url:
        db_url = settings.database_url.replace("postgresql", "sqlite+aiosqlite")
    else:
        db_url = settings.database_url.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get document
        doc = await session.get(Document, document_id)
        if not doc:
            return

        # Update status to AI_ANALYSIS
        doc.current_status = DocumentStatus.AI_ANALYSIS
        doc.status_updated_at = datetime.utcnow()
        await session.commit()

        # Load the saved file for processing
        file_path = Path(storage_path) / filename
        if not file_path.exists():
            doc.current_status = DocumentStatus.AI_FLAGGED
            doc.status_updated_at = datetime.utcnow()
            await session.commit()
            await engine.dispose()
            return

        # Re-open the file and run validation again
        with open(file_path, "rb") as f:
            validation = await validate_upload(f, filename, student_id)

        if not validation.is_valid:
            doc.current_status = DocumentStatus.REJECTED
            doc.status_updated_at = datetime.utcnow()
            await session.commit()
            await engine.dispose()
            return

        doc.sha256_hash = validation.sha256_hash
        doc.page_count = validation.page_count
        await session.commit()

        # Extract text
        with open(file_path, "rb") as f:
            extraction = await extract_text(f, filename)

        if not extraction.success:
            doc.current_status = DocumentStatus.AI_FLAGGED
            doc.status_updated_at = datetime.utcnow()
            await session.commit()
            await engine.dispose()
            return

        # Classify
        request = AIVerifyRequest(
            document_id=document_id,
            extracted_text=extraction.text,
            filename=filename,
        )

        result = await classify_document(request)

        # Store verification record
        verification = DocumentAIVerification(
            document_id=document_id,
            extracted_text_summary=result.summary,
            detected_category=result.category,
            detected_subject=result.detected_subject,
            detected_topics=result.detected_topics,
            confidence_score=float(result.confidence),
            is_academic=result.is_academic,
            quality_status=result.quality_status,
            suspicious_flags=result.suspicious_flags,
            ai_recommendation=result.ai_recommendation,
            model_name=result.model_name,
            verification_status=VerificationStatus.VERIFIED if result.is_academic else VerificationStatus.MANUAL_REQUIRED,
        )
        session.add(verification)

        # Update document status based on recommendation
        if result.confidence >= settings.ai_min_confidence_to_auto_review:
            doc.current_status = DocumentStatus.PENDING_ADMIN_REVIEW
        else:
            doc.current_status = DocumentStatus.AI_FLAGGED

        doc.status_updated_at = datetime.utcnow()
        await session.commit()

    await engine.dispose()


# ============================================================================
# Routes
# ============================================================================

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    student_name: str,
    student_id: int,
    file: UploadFile = File(...),
):
    """Student uploads a PDF for verification.

    Returns document ID; verification runs asynchronously.
    """
    # Read file into memory for validation
    content = await file.read()

    # Create upload directory
    upload_dir = Path(settings.storage_local_path) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    ext = Path(file.filename or "upload.pdf").suffix or ".pdf"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = str(upload_dir / unique_name)

    # Save file
    with open(storage_path, "wb") as f:
        f.write(content)

    # Calculate hash
    sha256 = hashlib.sha256(content).hexdigest()

    # Create document record
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    if "sqlite" in settings.database_url:
        db_url = settings.database_url.replace("postgresql", "sqlite+aiosqlite")
    else:
        db_url = settings.database_url.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        doc = Document(
            filename=unique_name,
            original_filename=file.filename or "upload.pdf",
            file_path=storage_path,
            file_size=len(content),
            mime_type=file.content_type or "application/pdf",
            sha256_hash=sha256,
            page_count=0,
            is_ocr=False,
            student_id=student_id,
            student_name=student_name,
            current_status=DocumentStatus.FILE_VALIDATION,
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    await engine.dispose()

    # Schedule background verification
    background_tasks.add_task(
        run_verification_pipeline,
        doc_id,
        storage_path,
        unique_name,
        student_id,
        student_name,
    )

    return UploadResponse(
        document_id=doc_id,
        filename=file.filename or "upload.pdf",
        file_size=len(content),
        status="UPLOADED",
        message="Document received. Verification in progress.",
    )


@router.get("/documents", response_model=list[DocumentResponse])
@limiter.limit("30/minute")
async def list_documents(request: Request, skip: int = 0, limit: int = 50):
    """List documents (admin endpoint)."""
    from sqlalchemy import select as sql_select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    if "sqlite" in settings.database_url:
        db_url = settings.database_url.replace("postgresql", "sqlite+aiosqlite")
    else:
        db_url = settings.database_url.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            sql_select(Document).order_by(Document.uploaded_at.desc()).offset(skip).limit(limit)
        )
        docs = result.scalars().all()

    await engine.dispose()

    return [doc.to_dict() for doc in docs]


@router.get("/documents/{doc_id}", response_model=DocumentDetailResponse)
@limiter.limit("30/minute")
async def get_document(request: Request, doc_id: int):
    """Get document details with latest verification."""
    from sqlalchemy import select as sql_select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    if "sqlite" in settings.database_url:
        db_url = settings.database_url.replace("postgresql", "sqlite+aiosqlite")
    else:
        db_url = settings.database_url.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        doc = await session.get(Document, doc_id)
        if not doc:
            await engine.dispose()
            raise HTTPException(status_code=404, detail="Document not found")

        # Get latest verification
        latest = (
            await session.execute(
                sql_select(DocumentAIVerification)
                .where(DocumentAIVerification.document_id == doc_id)
                .order_by(DocumentAIVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    await engine.dispose()

    return DocumentDetailResponse(
        **doc.to_dict(),
        verification=latest.to_dict() if latest else None,
    )


@router.post("/admin/action", response_model=AdminActionResponse)
@limiter.limit("20/minute")
async def admin_action(
    request: Request,
    creds: HTTPBasicCredentials = Depends(HTTPBasic()),
    action_data: AdminActionRequest = Body(...),
):
    """Admin takes action on a document.

    Actions:
    - approve: Mark as APPROVED
    - reject: Mark as REJECTED
    - request_manual_review: Keep in PENDING_ADMIN_REVIEW
    """
    if creds.username not in _valid_admins:
        raise HTTPException(status_code=403, detail="Admin access required")

    if "sqlite" in settings.database_url:
        db_url = settings.database_url.replace("postgresql", "sqlite+aiosqlite")
    else:
        db_url = settings.database_url.replace("postgresql", "postgresql+asyncpg")

    from sqlalchemy import select as sql_select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        doc = await session.get(Document, action_data.document_id)
        if not doc:
            await engine.dispose()
            raise HTTPException(status_code=404, detail="Document not found")

        if action_data.action == "approve":
            doc.current_status = DocumentStatus.APPROVED
        elif action_data.action == "reject":
            doc.current_status = DocumentStatus.REJECTED
        elif action_data.action == "request_manual_review":
            doc.current_status = DocumentStatus.PENDING_ADMIN_REVIEW

        doc.status_updated_at = datetime.utcnow()

        # Update latest verification admin decision
        latest_ver = (
            await session.execute(
                sql_select(DocumentAIVerification)
                .where(DocumentAIVerification.document_id == action_data.document_id)
                .order_by(DocumentAIVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if latest_ver:
            latest_ver.admin_decided = True
            latest_ver.admin_decision_at = datetime.utcnow()
            latest_ver.admin_decision_by = creds.username
            if action_data.notes:
                if latest_ver.suspicious_flags is None:
                    latest_ver.suspicious_flags = []
                latest_ver.suspicious_flags.append(action_data.notes)

        await session.commit()

        new_status = doc.current_status.value

    await engine.dispose()

    return AdminActionResponse(
        success=True,
        document_id=action_data.document_id,
        new_status=new_status,
        message=f"Document {action_data.action}d by {creds.username}",
    )