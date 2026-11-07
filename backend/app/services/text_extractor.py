"""Step 2: Text extraction service.

Extracts text from PDFs for AI classification.
Handles both native text PDFs and scanned/image-based PDFs (via OCR).
"""
from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader
from pypdf.exceptions import PdfReadError

from app.config import settings
from app.schemas.document import TextExtractionResult

log = logging.getLogger(__name__)


class TextExtractor:
    """Extracts text from PDF files with OCR fallback."""

    def __init__(self, file: BinaryIO, filename: str):
        self._file = file
        self._filename = filename

    async def extract(self) -> TextExtractionResult:
        """Extract text from PDF, using OCR for image-based PDFs."""
        # Read file into memory for pypdf
        content = await self._read_content()

        # Try direct text extraction first
        try:
            result = self._extract_native(content)
            if result.success and self._has_meaningful_text(result.text):
                return result
        except Exception as e:
            log.warning(f"Native extraction failed: {e}")

        # Fall back to OCR if enabled
        if settings.ocr_enabled:
            log.info("Falling back to OCR extraction")
            return await self._extract_ocr(content)

        return TextExtractionResult(success=False, text="", error="OCR not enabled")

    async def _read_content(self) -> bytes:
        """Read entire file content."""
        return self._file.read()

    def _extract_native(self, content: bytes) -> TextExtractionResult:
        """Extract text from PDF using native text layer."""
        try:
            reader = PdfReader(io.BytesIO(content))
            page_count = len(reader.pages)

            if page_count > settings.max_pdf_pages:
                return TextExtractionResult(
                    success=False,
                    text="",
                    error=f"PDF has {page_count} pages, max allowed is {settings.max_pdf_pages}",
                    page_count=page_count,
                )

            text_parts = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text_parts.append(text)
                if i >= 50:  # Safety limit
                    break

            full_text = "\n".join(text_parts)

            # Check for meaningful content
            is_ocr = not self._has_meaningful_text(full_text)

            return TextExtractionResult(
                success=True,
                text=full_text,
                is_ocr=is_ocr,
                page_count=page_count,
                metadata={"extraction_method": "native", "page_count": page_count},
            )

        except PdfReadError as e:
            return TextExtractionResult(
                success=False, text="", error=f"PDF parse error: {e}"
            )

    def _has_meaningful_text(self, text: str, threshold: float = 0.3) -> bool:
        """Check if extracted text has meaningful content.

        Threshold: at least 30% non-whitespace characters should be actual text.
        Pure whitespace extraction typically means OCR-only or corrupted.
        """
        if not text:
            return False
        stripped = text.strip()
        if not stripped:
            return False
        # Check ratio of non-whitespace
        non_ws = sum(1 for c in stripped if not c.isspace())
        return (non_ws / len(stripped)) >= threshold

    async def _extract_ocr(self, content: bytes) -> TextExtractionResult:
        """Extract text using OCR (pdf2image + pytesseract)."""
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
        except ImportError:
            return TextExtractionResult(
                success=False,
                text="",
                error="OCR libraries not installed (pytesseract, pdf2image)",
            )

        try:
            # Convert PDF to images
            images = convert_from_bytes(
                content, dpi=settings.ocr_dpi, first_page=1, last_page=settings.ocr_max_pages
            )

            if not images:
                return TextExtractionResult(
                    success=False, text="", error="No images extracted from PDF"
                )

            # Run OCR on each image
            text_parts = []
            for img in images:
                text = pytesseract.image_to_string(
                    img, lang=settings.ocr_language.split("+")[0]
                )
                text_parts.append(text)

            full_text = "\n".join(text_parts)

            return TextExtractionResult(
                success=True,
                text=full_text,
                is_ocr=True,
                page_count=len(images),
                metadata={"extraction_method": "ocr", "pages_converted": len(images)},
            )

        except Exception as e:
            log.exception("OCR extraction failed")
            return TextExtractionResult(success=False, text="", error=str(e))


async def extract_text(file: BinaryIO, filename: str) -> TextExtractionResult:
    """Convenience function to extract text from a PDF."""
    extractor = TextExtractor(file, filename)
    return await extractor.extract()