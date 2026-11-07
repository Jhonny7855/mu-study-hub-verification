"""
MU STUDY HUB - AI Document Verification Bot

A self-contained service that automatically verifies student-uploaded PDF documents
before they enter the administrator approval queue.

Run with: uvicorn app.main:app --reload
Docker: docker build -t verification -f backend/Dockerfile .
"""
from __future__ import annotations

import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        AI Document Verification Bot for MU STUDY HUB

        An intelligent academic-content filter that automatically checks uploaded
        PDF documents for relevance to education, learning, research, and examination.

        **Workflow:**
        1. File Validation – Check extension, MIME type, PDF signature, file size
        2. Text Extraction – Native PDF text, OCR for scanned docs
        3. AI Classification – Classify into 14 academic categories

        **Confidence-based routing:**
        - ≥85%: APPROVE_FOR_ADMIN_REVIEW (high confidence)
        - 60-84: MANUAL_REVIEW_REQUIRED (uncertain)
        - <60: FLAG_AS_SUSPICIOUS (low confidence)

        The administrator ALWAYS makes the final decision.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.middleware import SlowAPIMiddleware

    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # Exception handler for rate limiting
    from slowapi import _rate_limit_exceeded_handler
    app.add_exception_handler(Exception, _rate_limit_exceeded_handler)

    return app


app = create_app()

# Include API router
app.include_router(api_router, prefix="/api/v1")


# ============================================================================
# Startup/Shutdown events
# ============================================================================

@app.on_event("startup")
async def on_startup():
    """Initialize services on startup."""
    log.info("%s v%s starting...", settings.app_name, settings.app_version)

    # Create storage directory
    from pathlib import Path
    storage_path = Path(settings.storage_local_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    log.info("Storage path: %s", storage_path.absolute())

    # Initialize database
    await init_database()


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on shutdown."""
    log.info("Shutting down...")


async def init_database():
    """Create database tables."""
    from sqlalchemy import exc
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.models import Base

    url = settings.database_url
    if "sqlite" not in url:
        url = url.replace("postgresql", "postgresql+asyncpg")

    engine = create_async_engine(url, echo=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("Database tables created")
    except exc.SQLAlchemyError as e:
        log.warning("Database initialization warning: %s", e)
    finally:
        await engine.dispose()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "ai_engine": settings.ai_engine,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        workers=1,
    )