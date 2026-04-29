from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import EmailAccount, Provider
from app.db.session import get_db
from app.services.credential_store import get_gmail_tokens, get_yahoo_app_password, set_gmail_tokens
from app.services.gmail_token_refresh import GmailRefreshError, refresh_access_token
from app.services.yahoo_imap_fetch import YahooFetchError, list_folders
from app.settings import get_settings


router = APIRouter(tags=["gmail"])


def _gmail_get(path: str, access_token: str) -> httpx.Response:
    with httpx.Client(timeout=20.0) as client:
        return client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/{path}",
            headers={"Authorization": f"Bearer {access_token}"},
        )


def _gmail_get_label_detail(access_token: str, label_id: str) -> httpx.Response:
    with httpx.Client(timeout=20.0) as client:
        return client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/labels/{label_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )


@router.get("/labels-filters")
def labels_filters(account_id: int, db: Session = Depends(get_db)) -> dict:
    """
    Returns Gmail labels (system + user) and filter rules for an account.
    If filter scope is missing, labels are still returned and filters_error is set.
    """
    settings = get_settings()
    account = db.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.provider == Provider.yahoo:
        app_password = get_yahoo_app_password(db, settings, account.id)
        if not app_password:
            raise HTTPException(status_code=409, detail="Yahoo credentials missing. Reconnect in Settings.")
        try:
            folders = list_folders(email_address=account.email, app_password=app_password)
        except YahooFetchError as e:
            raise HTTPException(status_code=400, detail=f"Failed to load Yahoo folders: {e}") from e
        return {
            "labels": [
                {
                    "id": f,
                    "name": f,
                    "type": "folder",
                    "messages_total": None,
                    "messages_unread": None,
                }
                for f in folders
            ],
            "filters": [],
            "filters_error": None,
        }
    if account.provider != Provider.gmail:
        raise HTTPException(status_code=409, detail="Unsupported provider")

    tokens = get_gmail_tokens(db, settings, account.id)
    if not tokens:
        raise HTTPException(status_code=409, detail="Gmail credentials missing. Reconnect in Settings.")

    access_token = tokens.access_token

    def get_with_refresh(path: str) -> httpx.Response:
        nonlocal access_token
        res = _gmail_get(path, access_token)
        if res.status_code != 401:
            return res
        if not (tokens.refresh_token and settings.gmail_client_id and settings.gmail_client_secret):
            return res
        try:
            refreshed = refresh_access_token(
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret,
                refresh_token=tokens.refresh_token,
            )
        except GmailRefreshError:
            return res
        access_token = refreshed.access_token
        set_gmail_tokens(
            db,
            settings,
            account.id,
            access_token=access_token,
            refresh_token=tokens.refresh_token,
            expires_at=refreshed.expires_at,
            scope=refreshed.scope or tokens.scope,
            token_type=refreshed.token_type or tokens.token_type,
        )
        db.commit()
        return _gmail_get(path, access_token)

    labels_res = get_with_refresh("labels")
    if labels_res.status_code == 401:
        raise HTTPException(status_code=409, detail="Gmail authorization expired. Reconnect in Settings.")
    if labels_res.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Failed to load labels: {labels_res.text}")

    labels_payload = labels_res.json()
    labels_raw = labels_payload.get("labels", []) or []
    labels: list[dict[str, Any]] = []
    for l in labels_raw:
        label_id = l.get("id")
        messages_total = l.get("messagesTotal")
        messages_unread = l.get("messagesUnread")
        # labels.list often omits counts; best-effort fetch detail for each label.
        if label_id and (messages_total is None or messages_unread is None):
            detail = get_with_refresh(f"labels/{label_id}")
            if detail.status_code < 400:
                dp = detail.json()
                messages_total = dp.get("messagesTotal", messages_total)
                messages_unread = dp.get("messagesUnread", messages_unread)
        labels.append(
            {
                "id": label_id,
                "name": l.get("name"),
                "type": l.get("type"),
                "messages_total": messages_total,
                "messages_unread": messages_unread,
            }
        )
    labels.sort(key=lambda x: ((x.get("type") != "system"), str(x.get("name") or "").lower()))

    filters_res = get_with_refresh("settings/filters")
    filters_error: str | None = None
    filters: list[dict[str, Any]] = []
    if filters_res.status_code == 403:
        filters_error = "Gmail filter access denied (likely missing gmail.settings.basic scope). Reconnect Gmail with updated scopes."
    elif filters_res.status_code >= 400:
        filters_error = f"Failed to load filters: {filters_res.text}"
    else:
        filters_payload = filters_res.json()
        filters_raw = filters_payload.get("filter", []) or []
        for f in filters_raw:
            crit = f.get("criteria") or {}
            action = f.get("action") or {}
            filters.append(
                {
                    "id": f.get("id"),
                    "criteria": {
                        "from": crit.get("from"),
                        "to": crit.get("to"),
                        "subject": crit.get("subject"),
                        "query": crit.get("query"),
                        "negated_query": crit.get("negatedQuery"),
                        "has_attachment": crit.get("hasAttachment"),
                        "exclude_chats": crit.get("excludeChats"),
                        "size": crit.get("size"),
                        "size_comparison": crit.get("sizeComparison"),
                    },
                    "action": {
                        "add_label_ids": action.get("addLabelIds", []) or [],
                        "remove_label_ids": action.get("removeLabelIds", []) or [],
                        "forward": action.get("forward"),
                    },
                }
            )

    return {"labels": labels, "filters": filters, "filters_error": filters_error}

