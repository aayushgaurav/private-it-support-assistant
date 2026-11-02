from fastapi import Query

import logging
import time
import uuid
from collections import defaultdict
from pathlib import Path
from threading import Lock

from app.services.audit_service import log_action
from app.services.upload_validator import validate_upload

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select, func

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas import (
    TokenResponse,
    UserRegister,
    UserResponse,
)
from app.core.auth import get_current_user, require_role
from app.database.connection import get_db
from app.database.models import User, AuditLog
from app.rag.answer import ask_question
from app.services.auth_service import login_user, register_user
from app.services.document_processor import (
    delete_processed_document,
    list_processed_documents,
    process_document,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------
# UPLOAD RATE LIMITER
# In-memory, per-user. Resets on server restart.
# Limitation: does not persist across multiple worker
# processes. For multi-worker deployments, replace with
# a Redis-backed limiter (e.g. slowapi + Redis).
# --------------------------------------------------

UPLOAD_RATE_LIMIT   = 10          # max uploads
UPLOAD_RATE_WINDOW  = 3600        # per second window (1 hour)

_upload_counts: dict[int, list[float]] = defaultdict(list)
_rate_lock = Lock()


def _check_upload_rate(user_id: int) -> None:
    """Raise HTTP 429 if the user has exceeded the upload rate limit."""
    now = time.monotonic()
    with _rate_lock:
        timestamps = _upload_counts[user_id]
        # Discard timestamps outside the current window
        _upload_counts[user_id] = [
            t for t in timestamps if now - t < UPLOAD_RATE_WINDOW
        ]
        if len(_upload_counts[user_id]) >= UPLOAD_RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Upload limit reached. "
                    f"Maximum {UPLOAD_RATE_LIMIT} uploads per hour."
                ),
            )
        _upload_counts[user_id].append(now)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

app = FastAPI(
    title="Private AI IT Support Assistant",
    description="A local-first AI-powered IT support assistant",
    version="1.0.0",
)

# ADD CORS HERE — you already have it
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
PROJECT_DIR = Path(__file__).resolve().parents[1]
DOCUMENT_DIR = PROJECT_DIR / "data" / "documents"

DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

ALLOWED_ACCESS_LEVELS = {
    "ALL_EMPLOYEES",
    "ADMIN_ONLY",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# --------------------------------------------------
# REQUEST SCHEMAS
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000
    )


# --------------------------------------------------
# 1. HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to Private AI IT Support Assistant",
        "status": "running",
        "documentation": "/docs",
    }


# --------------------------------------------------
# 2. HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "private-ai-it-support",
    }


# --------------------------------------------------
# 3. USER REGISTRATION
# --------------------------------------------------

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(db, user_data)
        return user

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error


# --------------------------------------------------
# 4. USER LOGIN
# --------------------------------------------------

@app.post("/auth/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        token = login_user(
            db=db,
            username=form_data.username,
            password=form_data.password,
        )

        user = db.scalar(
            select(User).where(
                User.username == form_data.username.strip()
            )
        )

        if user:
            log_action(
                db=db,
                action="USER_LOGIN",
                user_id=user.id,
                details={
                    "status": "SUCCESS",
                    "role": user.role,
                },
            )

        return token

    except ValueError as error:
        log_action(
            db=db,
            action="USER_LOGIN_FAILED",
            user_id=None,
            details={
                "status": "FAILED",
                "attempted_username": form_data.username.strip(),
            },
        )

        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
# --------------------------------------------------
# 5. CURRENT USER PROFILE
# --------------------------------------------------

@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


# --------------------------------------------------
# 6. AI QUESTION-ANSWERING ENDPOINT
# --------------------------------------------------


@app.post("/ask")
def ask(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Step 1: Process the user's question

        result = ask_question(
            question=request.question,
            user_role=current_user.role,
        )

        # Step 2: Record the AI query event

        log_action(
            db=db,
            action="AI_QUERY",
            user_id=current_user.id,
            details={
                "user_role": current_user.role,
                "status": "SUCCESS",
            },
        )

        # Step 3: Return the AI response

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question.",
        ) from error

# --------------------------------------------------
# 7. DOCUMENT UPLOAD ENDPOINT
# ADMIN ONLY
# --------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    access_level: str = Form(...),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):

    # Step 0: Rate limit check (before any I/O)
    _check_upload_rate(current_user.id)

    # Step 1: Validate access level

    access_level = access_level.strip().upper()

    if access_level not in ALLOWED_ACCESS_LEVELS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid access level.",
                "allowed_values": list(ALLOWED_ACCESS_LEVELS),
                "received_value": access_level,
            },
        )

    # Step 2: Validate file extension — strip directory components first
    original_name = Path(file.filename or "").name
    # Additional sanitization: reject names that are empty after stripping
    if not original_name or original_name in (".", ".."):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are supported.",
        )

    # Step 3: Read file with a size limit

    file_content = await file.read(MAX_FILE_SIZE + 1)

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB.",
        )

    # Step 4: Generate a safe UUID-based filename
    document_id = uuid.uuid4().hex
    stored_name = f"{document_id}{extension}"
    file_path = DOCUMENT_DIR / stored_name

    # Step 4a: Validate content (magic bytes, DOCX structure, TXT encoding)
    # and confirm destination path stays inside DOCUMENT_DIR.
    # Runs entirely in memory — nothing written to disk yet.
    validate_upload(
        file_content=file_content,
        extension=extension,
        original_name=original_name,
        document_dir=DOCUMENT_DIR,
        document_id=document_id,
    )

    # Step 5: Save the uploaded file

    try:
        file_path.write_bytes(file_content)

        # Step 6: Extract, chunk, embed and index document

        processing_result = process_document(
            file_path=file_path,
            document_id=document_id,
            original_filename=original_name,
            access_level=access_level,
        )

        log_action(
        db=db,
        action="DOCUMENT_UPLOAD",
        user_id=current_user.id,
        document_id=document_id,
        details={
            "filename": original_name,
            "access_level": access_level,
         },
        )

        return {
            "message": "Document uploaded and processed successfully.",
            "document_id": document_id,
            "original_filename": original_name,
            "stored_filename": stored_name,
            "access_level": access_level,
            "uploaded_by": current_user.username,
            "processing": processing_result,
        }

    except ValueError as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    except Exception as error:
        file_path.unlink(missing_ok=True)
        # Compensating cleanup: process_document may have written ChromaDB
        # chunks before the failure (e.g. log_action raised after indexing
        # succeeded). Delete them now so no orphaned vectors remain.
        # This is safe: delete_processed_document filters by document_id,
        # so it cannot affect any other document's chunks.
        try:
            delete_processed_document(document_id, DOCUMENT_DIR)
        except Exception as cleanup_err:
            logger.error(
                "Post-failure ChromaDB cleanup failed for document_id=%s: %s",
                document_id,
                cleanup_err,
            )
        logger.error("Unexpected upload failure for document_id=%s: %s", document_id, error)
        raise HTTPException(
            status_code=500,
            detail="Document processing failed.",
        ) from error

    finally:
        await file.close()


# --------------------------------------------------
# 8. LIST DOCUMENTS
# ADMIN ONLY
# --------------------------------------------------

@app.get("/documents")
def get_documents(
    current_user: User = Depends(require_role("admin")),
):
    documents = list_processed_documents()

    return {
        "total_documents": len(documents),
        "documents": documents,
    }


# --------------------------------------------------
# 9. DELETE DOCUMENT
# ADMIN ONLY
# --------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):

    # Step 1: Validate document ID format

    try:
        uuid.UUID(hex=document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        )

    try:
        # Step 2: Delete document chunks and physical file

        result = delete_processed_document(document_id, DOCUMENT_DIR)

        if result["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

        # Step 3: Record the deletion outcome in the audit log

        log_action(
            db=db,
            action="DOCUMENT_DELETE",
            user_id=current_user.id,
            document_id=document_id,
            details={
                "deleted_by": current_user.username,
                "deleted_chunks": result["deleted_chunks"],
                "deleted_file": result["deleted_file"],
                "file_error": result["file_error"],
                "status": result["status"],
            },
        )

        # Step 4: Build response — be honest about partial deletion

        partial = not result["deleted_file"] and result["file_error"] is not None

        return {
            "message": (
                "Document removed. The physical file could not be deleted."
                if partial else
                "Document deleted successfully."
            ),
            "document_id": document_id,
            "deleted_by": current_user.username,
            "deleted_chunks": result["deleted_chunks"],
            "deleted_file": result["deleted_file"],
            "status": result["status"],
            "audit_logged": True,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to delete document.",
        ) from error

# --------------------------------------------------
# 10. ADMIN DASHBOARD
# ADMIN ONLY
# --------------------------------------------------

@app.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_role("admin")),
):
    return {
        "message": "Welcome to the admin dashboard.",
        "username": current_user.username,
        "role": current_user.role,
    }

#audit logs endpoint
@app.get("/admin/audit-logs")
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None, max_length=50),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    # Build the database query
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    # Apply optional action filter
    if action:
        action = action.strip().upper()
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(
            AuditLog.action == action
        )

    # Count matching records
    total = db.scalar(count_query)

    # Retrieve one page of records
    logs = db.scalars(
        query
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "audit_logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "document_id": log.document_id,
                "details": log.details,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }


