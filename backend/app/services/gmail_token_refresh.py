from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx


@dataclass(frozen=True)
class RefreshedToken:
    access_token: str
    expires_at: datetime | None
    scope: str | None
    token_type: str | None


class GmailRefreshError(Exception):
    pass


def refresh_access_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> RefreshedToken:
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(token_url, data=data)
        if res.status_code >= 400:
            raise GmailRefreshError(res.text)
        payload = res.json()
    except GmailRefreshError:
        raise
    except Exception as e:  # noqa: BLE001
        raise GmailRefreshError(str(e)) from e

    access_token = payload.get("access_token")
    if not access_token:
        raise GmailRefreshError("No access_token in refresh response")
    expires_in = payload.get("expires_in")
    expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None
    return RefreshedToken(
        access_token=access_token,
        expires_at=expires_at,
        scope=payload.get("scope"),
        token_type=payload.get("token_type"),
    )

