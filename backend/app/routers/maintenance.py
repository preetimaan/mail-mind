from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import EmailMessage
from app.db.session import get_db


router = APIRouter(tags=["maintenance"])


@router.post("/maintenance/dedupe/messages")
def dedupe_messages(db: Session = Depends(get_db)) -> dict:
    """
    Safety tool: remove duplicates by (account_id, external_id) keeping the lowest id.

    In normal operation we prevent duplicates via UNIQUE(account_id, external_id).
    This endpoint exists to clean up any legacy/dev DBs created before the constraint.
    """
    rows = db.execute(select(EmailMessage.account_id, EmailMessage.external_id, EmailMessage.id)).all()
    seen: set[tuple[int, str]] = set()
    to_delete: list[int] = []
    for account_id, external_id, mid in rows:
        key = (account_id, external_id)
        if key in seen:
            to_delete.append(mid)
        else:
            seen.add(key)

    if to_delete:
        db.execute(delete(EmailMessage).where(EmailMessage.id.in_(to_delete)))
        db.commit()
    return {"deleted": len(to_delete)}

