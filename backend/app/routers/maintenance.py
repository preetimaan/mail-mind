from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, EmailMessage, OAuthCredential, OAuthProvider, OAuthState, Provider
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


@router.post("/maintenance/oauth/cleanup")
def cleanup_oauth(db: Session = Depends(get_db)) -> dict:
    """
    Cleanup tool:
    - delete expired oauth_states
    - mark accounts inactive if credentials for their provider are missing
    """
    now = datetime.utcnow()
    expired = db.execute(delete(OAuthState).where(OAuthState.expires_at < now)).rowcount or 0

    accounts = db.execute(select(EmailAccount)).scalars().all()
    inactive_marked = 0
    for a in accounts:
        expected = OAuthProvider.gmail if a.provider == Provider.gmail else OAuthProvider.yahoo
        has = (
            db.execute(
                select(OAuthCredential.id).where(
                    OAuthCredential.account_id == a.id,
                    OAuthCredential.provider == expected,
                )
            )
            .scalars()
            .first()
            is not None
        )
        if not has and a.is_active:
            a.is_active = False
            inactive_marked += 1

    db.commit()
    return {"expired_states_deleted": int(expired), "accounts_marked_inactive": inactive_marked}

