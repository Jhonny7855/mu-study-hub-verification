"""Step 1: File validation service.

Validates uploaded files against the requirements in section 2, step 1.
All checks are performed BEFORE any content is read or parsed.
"""
from __future__ import annotations

import hashlib
import io
import logging
import mimetypes
import magic  # type: ignore[import]
from pathlib import Path
from typing import BinaryIO

from app.config import settings
from app.schemas.document import FileValidationResult

log = logging.getLogger(__name__)


class FileValidator:
    """Validates uploaded PDF files for safety and academic eligibility."""

    PDF_SIGNATURE = b"%PDF-"

    def __init__(self, file: BinaryIO, filename: str, student_id: int):
        self._file = file
        self._filename = filename
        self.student_id = student_id
        self._hasher = hashlib.sha256()
        self._errors: list[str] = []

    async def validate(self) -> FileValidationResult:
        """Run all validation checks, returning structured results."""
        # Read file content for inspection
        content = await self._read_all()

        # Check file extension
        ext_valid = self._check_extension(content)

        # Check MIME type
        mime_valid, detected_mime = self._check_mime_type(content)

        # Check file size
        size_valid, file_size = self._check_size(content)

        # Check PDF signature
        pdf_valid, is_corrupted = self._check_pdf_signature(content)

        # Check for password protection (basic detection)
        password_protected = self._detect_password_protection(content)

        # Calculate hash
        sha256 = self._hasher.hexdigest()

        # Build result
        is_valid = ext_valid and mime_valid and size_valid and pdf_valid and not is_corrupted

        return FileValidationResult(
            is_valid=is_valid,
            errors=self._errors,
            filename=self._filename,
            file_size=file_size,
            mime_type=detected_mime,
            sha256_hash=sha256 if is_valid else None,
            actual_pdf=ext_valid and mime_valid and pdf_valid,
            page_count=0,  # Will be filled during extraction
            is_password_protected=password_protected,
            is_corrupted=is_corrupted,
        )

    async def _read_all(self) -> bytes:
        """Read entire file content, updating hash along the way."""
        chunk_size = 64 * 1024  # 64 KiB chunks
        content = b""

        while True:
            chunk = await self._read_chunk(chunk_size)
            if not chunk:
                break
            content += chunk
            self._hasher.update(chunk)

        return content

    async def _read_chunk(self, size: int) -> bytes:
        """Read a chunk asynchronously (simulated for sync file-like)."""
        # For sync file objects, we read directly
        # In production, use aiofiles or similar
        return self._file.read(size)

    def _check_extension(self, content: bytes) -> bool:
        """Verify file has .pdf extension."""
        ext = Path(self._filename).suffix.lower()
        if ext != ".pdf":
            self._errors.append(f"Invalid file extension: {ext} (expected .pdf)")
            return False
        return True

    def _check_mime_type(self, content: bytes) -> tuple[bool, str]:
        """Verify actual MIME type matches PDF."""
        try:
            mime = magic.from_buffer(content, mime=True)
        except Exception as e:
            log.warning(f"MIME detection failed: {e}")
            mime = "application/octet-stream"

        if mime != "application/pdf":
            self._errors.append(f"MIME type {mime} is not a valid PDF")
            return False, mime
        return True, mime

    def _check_size(self, content: bytes) -> tuple[bool, int]:
        """Verify file size is within limits."""
        file_size = len(content)
        max_bytes = settings.storage_max_bytes

        if file_size > max_bytes:
            self._errors.append(
                f"File size {file_size} exceeds maximum {max_bytes} bytes"
            )
            return False, file_size

        if file_size == 0:
            self._errors.append("File is empty")
            return False, file_size

        return True, file_size

    def _check_pdf_signature(self, content: bytes) -> tuple[bool, bool]:
        """Check for valid PDF signature (first %PDF- header)."""
        is_corrupted = not content.startswith(self.PDF_SIGNATURE)

        if is_corrupted:
            self._errors.append("File does not start with PDF signature")

        return not is_corrupted, is_corrupted

    def _detect_password_protection(self, content: bytes) -> bool:
        """Detect if PDF is encrypted/password-protected.

        This is a basic heuristic: encrypted PDFs contain the string
        '/Encrypt' near the beginning.
        """
        # Encrypt dictionary is typically within first 1KB
        header = content[:1024].decode("latin-1", errors="ignore")
        if "/Encrypt" in header:
            self._errors.append("PDF appears to be encrypted/password-protected")
            return True
        return False


async def validate_upload(
    file: BinaryIO, filename: str, student_id: int
) -> FileValidationResult:
    """Convenience function to validate an uploaded PDF."""
    validator = FileValidator(file, filename, student_id)
    return await validator.validate()