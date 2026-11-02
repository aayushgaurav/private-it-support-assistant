"""
upload_validator.py

Pre-write validation for uploaded documents.
All checks run against the raw bytes in memory — nothing is written to disk first.

Validates:
- PDF magic bytes
- DOCX ZIP signature and required internal structure
- TXT UTF-8 decodability
- Resolved destination path stays inside DOCUMENT_DIR (path traversal)
"""

import io
import logging
import zipfile
from pathlib import Path

from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Magic-byte constants
# ---------------------------------------------------------------------------

_PDF_MAGIC  = b"%PDF-"
_ZIP_MAGIC  = b"PK\x03\x04"

# Required entries every valid DOCX must contain
_DOCX_REQUIRED = {"[Content_Types].xml", "word/document.xml"}

# ZIP-bomb limits applied during DOCX central-directory inspection.
#
# Limitation: ZipFile.infolist() materialises the entire central directory
# into memory before iteration begins. These limits therefore protect against
# decompression exhaustion but NOT against a maliciously large central
# directory itself. The existing 10 MB upload cap is the primary defence
# against oversized compressed payloads reaching this point.
_DOCX_MAX_ENTRIES        = 1_000
_DOCX_MAX_ENTRY_SIZE     = 50  * 1024 * 1024   # 50 MB per single entry
_DOCX_MAX_TOTAL_SIZE     = 100 * 1024 * 1024   # 100 MB total uncompressed

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_upload(
    file_content: bytes,
    extension: str,
    original_name: str,
    document_dir: Path,
    document_id: str,
) -> None:
    """
    Validate file content and destination path before writing to disk.

    Raises HTTPException (400 / 415) on any validation failure.
    Never raises 500 for user-supplied content issues.
    """
    _validate_destination_path(document_dir, document_id, extension)

    if extension == ".pdf":
        _validate_pdf(file_content)
    elif extension == ".docx":
        _validate_docx(file_content)
    elif extension == ".txt":
        _validate_txt(file_content)


# ---------------------------------------------------------------------------
# Path containment check
# ---------------------------------------------------------------------------

def _validate_destination_path(
    document_dir: Path,
    document_id: str,
    extension: str,
) -> None:
    """
    Confirm the resolved destination path stays strictly inside document_dir.

    document_id is a uuid4().hex value (32 hex chars) — server-generated and
    safe — but we validate defensively anyway.
    """
    destination = (document_dir / f"{document_id}{extension}").resolve()
    resolved_dir = document_dir.resolve()

    # Use is_relative_to (Python 3.9+) for a reliable containment check
    try:
        destination.relative_to(resolved_dir)
    except ValueError:
        logger.error(
            "Path traversal attempt blocked: destination=%s dir=%s",
            destination,
            resolved_dir,
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid upload destination.",
        )


# ---------------------------------------------------------------------------
# PDF validation
# ---------------------------------------------------------------------------

def _validate_pdf(content: bytes) -> None:
    """Reject content that does not start with the PDF signature."""
    if not content.startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=415,
            detail="File content does not match PDF format.",
        )


# ---------------------------------------------------------------------------
# DOCX validation
# ---------------------------------------------------------------------------

def _validate_docx(content: bytes) -> None:
    """
    Validate DOCX content:
    1. Must start with the ZIP magic bytes.
    2. Must be a readable ZIP archive.
    3. Must contain [Content_Types].xml and word/document.xml.
    4. Entry count must not exceed _DOCX_MAX_ENTRIES.
    5. No single entry may claim an uncompressed size above _DOCX_MAX_ENTRY_SIZE.
    6. Total uncompressed size across all entries must not exceed _DOCX_MAX_TOTAL_SIZE.

    Checks 4-6 read only ZipInfo metadata (no decompression occurs here).
    Note: ZipFile.infolist() materialises the full central directory before
    iteration, so the entry-count limit does not prevent a large central
    directory from being allocated. The 10 MB upload cap is the primary
    guard against that scenario.
    """
    if not content.startswith(_ZIP_MAGIC):
        raise HTTPException(
            status_code=415,
            detail="File content does not match DOCX format.",
        )

    _INVALID = HTTPException(status_code=415, detail="File is not a valid DOCX document.")

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            entries = zf.infolist()

            if len(entries) > _DOCX_MAX_ENTRIES:
                raise _INVALID

            names = set()
            total_uncompressed = 0

            for info in entries:
                if info.file_size > _DOCX_MAX_ENTRY_SIZE:
                    raise _INVALID
                total_uncompressed += info.file_size
                if total_uncompressed > _DOCX_MAX_TOTAL_SIZE:
                    raise _INVALID
                names.add(info.filename)

            if _DOCX_REQUIRED - names:
                raise _INVALID

    except zipfile.BadZipFile:
        raise _INVALID
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during DOCX validation")
        raise _INVALID


# ---------------------------------------------------------------------------
# TXT validation
# ---------------------------------------------------------------------------

def _validate_txt(content: bytes) -> None:
    """
    Validate that the content is decodable as UTF-8.
    Legitimate multilingual UTF-8 text is accepted.
    """
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=415,
            detail=(
                "Text file could not be decoded as UTF-8. "
                "Please save the file as UTF-8 and try again."
            ),
        )
