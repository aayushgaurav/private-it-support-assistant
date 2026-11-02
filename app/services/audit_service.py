from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database.models import AuditLog


AUDIT_RETENTION_DAYS = 90


def log_action(
    db: Session,
    action: str,
    user_id: int | None = None,
    document_id: str | None = None,
    details: dict | None = None,
):
    """
    Delete audit records older than 90 days,
    then save the new audit event.
    """

    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=AUDIT_RETENTION_DAYS
    )

    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        document_id=document_id,
        details=details or {},
    )

    try:
        # Step 1: Remove expired audit records
        db.execute(
            delete(AuditLog).where(
                AuditLog.created_at < cutoff_date
            )
        )

        # Step 2: Save the new audit event
        db.add(audit_entry)

        db.commit()
        db.refresh(audit_entry)

        return audit_entry

    except Exception:
        db.rollback()
        raise