"""
tests/test_upload_security.py

Automated security tests for the document upload pipeline.

Isolation guarantees:
- All file operations use pytest tmp_path (deleted after each test).
- No production DOCUMENT_DIR, ChromaDB collection, or SQLite DB is touched.
- ChromaDB and vector_store calls are mocked throughout.
- Rate-limiter state is reset between tests via monkeypatch.
"""

import io
import time
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Helpers to build test file content
# ---------------------------------------------------------------------------

def make_valid_pdf() -> bytes:
    return b"%PDF-1.4 fake but valid-looking pdf content"


def make_fake_pdf() -> bytes:
    return b"This is not a PDF file at all."


def make_valid_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<document/>")
        zf.writestr("word/styles.xml", "<styles/>")
    return buf.getvalue()


def make_docx_missing_document_xml() -> bytes:
    """Valid ZIP but missing word/document.xml — not a real DOCX."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
    return buf.getvalue()


def make_corrupt_docx() -> bytes:
    """Starts with ZIP magic but is truncated/corrupt."""
    return b"PK\x03\x04" + b"\x00" * 20


def make_zip_not_docx() -> bytes:
    """Valid ZIP archive but no DOCX structure."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "just a zip")
    return buf.getvalue()


def make_valid_utf8_txt() -> bytes:
    return "Hello, world! Привет мир! 日本語テスト".encode("utf-8")


def make_invalid_encoding_txt() -> bytes:
    return b"\xff\xfe invalid latin-1 bytes \x80\x81"


# ---------------------------------------------------------------------------
# upload_validator tests
# ---------------------------------------------------------------------------

class TestValidatePDF:
    def test_valid_pdf_passes(self, tmp_path):
        from app.services.upload_validator import validate_upload
        validate_upload(make_valid_pdf(), ".pdf", "doc.pdf", tmp_path, "a" * 32)

    def test_fake_pdf_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_fake_pdf(), ".pdf", "fake.pdf", tmp_path, "a" * 32)
        assert exc.value.status_code == 415

    def test_docx_bytes_as_pdf_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_valid_docx(), ".pdf", "wrong.pdf", tmp_path, "a" * 32)
        assert exc.value.status_code == 415


class TestValidateDOCX:
    def test_valid_docx_passes(self, tmp_path):
        from app.services.upload_validator import validate_upload
        validate_upload(make_valid_docx(), ".docx", "doc.docx", tmp_path, "a" * 32)

    def test_corrupt_docx_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_corrupt_docx(), ".docx", "corrupt.docx", tmp_path, "a" * 32)
        assert exc.value.status_code == 415

    def test_zip_without_docx_structure_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_zip_not_docx(), ".docx", "fake.docx", tmp_path, "a" * 32)
        assert exc.value.status_code == 415

    def test_docx_missing_document_xml_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(
                make_docx_missing_document_xml(), ".docx", "partial.docx", tmp_path, "a" * 32
            )
        assert exc.value.status_code == 415

    def test_pdf_bytes_as_docx_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_valid_pdf(), ".docx", "wrong.docx", tmp_path, "a" * 32)
        assert exc.value.status_code == 415

    def test_plain_text_as_docx_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(b"not a zip", ".docx", "text.docx", tmp_path, "a" * 32)
        assert exc.value.status_code == 415


class TestValidateTXT:
    def test_valid_utf8_passes(self, tmp_path):
        from app.services.upload_validator import validate_upload
        validate_upload(make_valid_utf8_txt(), ".txt", "doc.txt", tmp_path, "a" * 32)

    def test_invalid_encoding_rejected(self, tmp_path):
        from app.services.upload_validator import validate_upload
        with pytest.raises(HTTPException) as exc:
            validate_upload(make_invalid_encoding_txt(), ".txt", "bad.txt", tmp_path, "a" * 32)
        assert exc.value.status_code == 415

    def test_empty_utf8_passes_validator(self, tmp_path):
        """Empty bytes decode as UTF-8 fine; emptiness is caught later by extract_document."""
        from app.services.upload_validator import validate_upload
        validate_upload(b"", ".txt", "empty.txt", tmp_path, "a" * 32)


# ---------------------------------------------------------------------------
# Path traversal tests
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_normal_uuid_path_passes(self, tmp_path):
        from app.services.upload_validator import _validate_destination_path
        doc_id = "a" * 32
        _validate_destination_path(tmp_path, doc_id, ".pdf")

    def test_posix_traversal_blocked(self, tmp_path):
        """
        document_id is always a uuid4().hex — server-generated.
        This test verifies the containment check itself works if somehow
        a crafted id were passed.
        """
        from app.services.upload_validator import _validate_destination_path
        # Simulate a crafted document_id that tries to escape
        evil_id = "../../../etc/passwd"
        with pytest.raises(HTTPException) as exc:
            _validate_destination_path(tmp_path, evil_id, "")
        assert exc.value.status_code == 400

    def test_windows_traversal_blocked(self, tmp_path):
        from app.services.upload_validator import _validate_destination_path
        evil_id = "..\\..\\windows\\system32\\evil"
        with pytest.raises(HTTPException) as exc:
            _validate_destination_path(tmp_path, evil_id, "")
        assert exc.value.status_code == 400

    def test_absolute_path_blocked(self, tmp_path):
        from app.services.upload_validator import _validate_destination_path
        evil_id = "/etc/passwd"
        with pytest.raises(HTTPException) as exc:
            _validate_destination_path(tmp_path, evil_id, "")
        assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# Rate limiter tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    def _reset_limiter(self, monkeypatch):
        """Reset the in-memory rate limiter state between tests."""
        import app.main as main_module
        from collections import defaultdict
        monkeypatch.setattr(main_module, "_upload_counts", defaultdict(list))

    def test_within_limit_passes(self, monkeypatch):
        self._reset_limiter(monkeypatch)
        from app.main import _check_upload_rate, UPLOAD_RATE_LIMIT
        for _ in range(UPLOAD_RATE_LIMIT):
            _check_upload_rate(user_id=999)

    def test_exceeding_limit_raises_429(self, monkeypatch):
        self._reset_limiter(monkeypatch)
        from app.main import _check_upload_rate, UPLOAD_RATE_LIMIT
        for _ in range(UPLOAD_RATE_LIMIT):
            _check_upload_rate(user_id=999)
        with pytest.raises(HTTPException) as exc:
            _check_upload_rate(user_id=999)
        assert exc.value.status_code == 429

    def test_limit_is_per_user(self, monkeypatch):
        """User 1 hitting the limit must not affect user 2."""
        self._reset_limiter(monkeypatch)
        from app.main import _check_upload_rate, UPLOAD_RATE_LIMIT
        for _ in range(UPLOAD_RATE_LIMIT):
            _check_upload_rate(user_id=1)
        # User 2 should still be allowed
        _check_upload_rate(user_id=2)

    def test_old_timestamps_expire(self, monkeypatch):
        """Timestamps outside the window should not count toward the limit."""
        self._reset_limiter(monkeypatch)
        import app.main as main_module
        from app.main import _check_upload_rate, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW

        # Pre-fill with timestamps that are just outside the window
        expired = time.monotonic() - UPLOAD_RATE_WINDOW - 1
        main_module._upload_counts[999] = [expired] * UPLOAD_RATE_LIMIT

        # Should not raise — all old timestamps are expired
        _check_upload_rate(user_id=999)


# ---------------------------------------------------------------------------
# process_document compensating cleanup tests
# ---------------------------------------------------------------------------

class TestProcessDocumentCleanup:
    """
    Verify that if ChromaDB indexing fails, any partially written chunks
    are cleaned up and the error is re-raised.
    """

    def _make_temp_txt(self, tmp_path: Path) -> Path:
        f = tmp_path / "test.txt"
        f.write_text("This is a test document with enough content to chunk.", encoding="utf-8")
        return f

    @patch("app.services.document_processor.vector_store")
    def test_chromadb_failure_triggers_cleanup(self, mock_vs, tmp_path):
        from app.services.document_processor import process_document

        file_path = self._make_temp_txt(tmp_path)

        # Simulate add_documents raising, then get returning some orphaned IDs
        mock_vs.add_documents.side_effect = RuntimeError("ChromaDB unavailable")
        mock_vs.get.return_value = {"ids": ["doc-0", "doc-1"], "metadatas": [{}, {}]}

        with pytest.raises(RuntimeError, match="ChromaDB unavailable"):
            process_document(
                file_path=file_path,
                document_id="b" * 32,
                original_filename="test.txt",
                access_level="ALL_EMPLOYEES",
            )

        # Compensating delete must have been called with the orphaned IDs
        mock_vs.delete.assert_called_once_with(ids=["doc-0", "doc-1"])

    @patch("app.services.document_processor.vector_store")
    def test_chromadb_failure_no_orphans_skips_delete(self, mock_vs, tmp_path):
        from app.services.document_processor import process_document

        file_path = self._make_temp_txt(tmp_path)

        mock_vs.add_documents.side_effect = RuntimeError("ChromaDB unavailable")
        mock_vs.get.return_value = {"ids": [], "metadatas": []}

        with pytest.raises(RuntimeError):
            process_document(
                file_path=file_path,
                document_id="c" * 32,
                original_filename="test.txt",
                access_level="ALL_EMPLOYEES",
            )

        # No orphans found — delete should NOT be called
        mock_vs.delete.assert_not_called()

    @patch("app.services.document_processor.vector_store")
    def test_parse_failure_never_reaches_chromadb(self, mock_vs, tmp_path):
        from app.services.document_processor import process_document

        # Write a file that will fail extraction (empty content)
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")

        with pytest.raises(ValueError):
            process_document(
                file_path=f,
                document_id="d" * 32,
                original_filename="empty.txt",
                access_level="ALL_EMPLOYEES",
            )

        # ChromaDB must never have been touched
        mock_vs.add_documents.assert_not_called()
        mock_vs.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Fix 1 — DOCX decompression limit tests
# ---------------------------------------------------------------------------

def _make_minimal_docx_bytes() -> bytes:
    """Return the smallest valid DOCX bytes; infolist() is patched in each test."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", "<document/>")
    return buf.getvalue()


class TestValidateDOCXDecompressionLimits:
    """Tests for ZIP-bomb / decompression-limit checks added in Fix 1."""

    def test_valid_docx_still_passes(self, tmp_path):
        """Existing valid DOCX must not be broken by the new limits."""
        from app.services.upload_validator import validate_upload
        validate_upload(make_valid_docx(), ".docx", "doc.docx", tmp_path, "a" * 32)

    def test_single_entry_exceeding_50mb_rejected(self, tmp_path):
        """
        A DOCX whose central directory contains one entry claiming
        file_size > 50 MB must be rejected without decompressing anything.
        """
        from app.services import upload_validator

        content = _make_minimal_docx_bytes()

        big_entry = MagicMock(spec=zipfile.ZipInfo)
        big_entry.file_size = 51 * 1024 * 1024   # 51 MB — over the 50 MB limit
        big_entry.filename = "[Content_Types].xml"

        normal_entry = MagicMock(spec=zipfile.ZipInfo)
        normal_entry.file_size = 1024
        normal_entry.filename = "word/document.xml"

        with patch("zipfile.ZipFile.infolist", return_value=[big_entry, normal_entry]):
            with pytest.raises(HTTPException) as exc:
                upload_validator._validate_docx(content)
        assert exc.value.status_code == 415

    def test_total_uncompressed_exceeding_100mb_rejected(self, tmp_path):
        """
        Multiple entries whose combined file_size exceeds 100 MB must be
        rejected even if each individual entry is below the 50 MB single-entry limit.
        """
        from app.services import upload_validator

        content = _make_minimal_docx_bytes()

        # Three entries of 40 MB each = 120 MB total; each is under the 50 MB limit
        entries = []
        for name in ["[Content_Types].xml", "word/document.xml", "word/styles.xml"]:
            e = MagicMock(spec=zipfile.ZipInfo)
            e.file_size = 40 * 1024 * 1024
            e.filename = name
            entries.append(e)

        with patch("zipfile.ZipFile.infolist", return_value=entries):
            with pytest.raises(HTTPException) as exc:
                upload_validator._validate_docx(content)
        assert exc.value.status_code == 415

    def test_entry_count_exceeding_1000_rejected(self, tmp_path):
        """A ZIP with more than 1,000 entries must be rejected."""
        from app.services import upload_validator

        content = _make_minimal_docx_bytes()

        entries = []
        for i in range(1001):
            e = MagicMock(spec=zipfile.ZipInfo)
            e.file_size = 100   # tiny — only the count matters here
            e.filename = f"word/chunk{i}.xml"
            entries.append(e)
        # Ensure required entries are present so only the count triggers rejection
        entries[0].filename = "[Content_Types].xml"
        entries[1].filename = "word/document.xml"

        with patch("zipfile.ZipFile.infolist", return_value=entries):
            with pytest.raises(HTTPException) as exc:
                upload_validator._validate_docx(content)
        assert exc.value.status_code == 415


# ---------------------------------------------------------------------------
# Fix 2 — audit-log failure triggers ChromaDB compensating cleanup
# ---------------------------------------------------------------------------

class TestAuditLogFailureCleanup:
    """
    Regression test: if log_action raises after process_document succeeds,
    delete_processed_document must be called with the correct document_id
    and DOCUMENT_DIR, and the endpoint must return HTTP 500.
    """

    @patch("app.main.delete_processed_document")
    @patch("app.main.log_action")
    @patch("app.main.process_document")
    @patch("app.main.validate_upload")
    def test_log_action_failure_triggers_chromadb_cleanup(
        self,
        mock_validate,
        mock_process,
        mock_log,
        mock_delete,
        tmp_path,
        monkeypatch,
    ):
        import asyncio
        from collections import defaultdict
        from unittest.mock import AsyncMock
        from app.main import upload_document, DOCUMENT_DIR
        from app.database.models import User

        # Reset rate limiter so this test is never blocked by a previous run
        import app.main as main_module
        monkeypatch.setattr(main_module, "_upload_counts", defaultdict(list))

        # process_document succeeds
        mock_validate.return_value = None
        mock_process.return_value = {
            "document_id": "e" * 32,
            "filename": "test.txt",
            "total_chunks": 2,
            "status": "processed successfully",
        }
        # log_action raises after ChromaDB indexing is done
        mock_log.side_effect = RuntimeError("SQLite unavailable")
        mock_delete.return_value = {
            "status": "deleted",
            "deleted_chunks": 2,
            "deleted_file": True,
            "file_error": None,
        }

        # Minimal fake UploadFile
        from fastapi import UploadFile
        fake_file = MagicMock(spec=UploadFile)
        fake_file.filename = "test.txt"
        fake_file.read = AsyncMock(return_value=b"hello world content")
        fake_file.close = AsyncMock()

        # Minimal fake admin user
        fake_user = MagicMock(spec=User)
        fake_user.id = 42
        fake_user.username = "testadmin"
        fake_user.role = "admin"

        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                upload_document(
                    file=fake_file,
                    access_level="ALL_EMPLOYEES",
                    current_user=fake_user,
                    db=MagicMock(),
                )
            )

        # Must return HTTP 500 with the safe generic message
        assert exc.value.status_code == 500
        assert exc.value.detail == "Document processing failed."

        # delete_processed_document must have been called exactly once
        mock_delete.assert_called_once()
        args = mock_delete.call_args.args

        # First arg: document_id — 32-char lowercase hex string
        called_doc_id = args[0]
        assert len(called_doc_id) == 32
        assert all(c in "0123456789abcdef" for c in called_doc_id)

        # Second arg: document_dir — must equal DOCUMENT_DIR
        assert args[1] == DOCUMENT_DIR
