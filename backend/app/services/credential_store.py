from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OAuthCredential, OAuthProvider
from app.services.token_crypto import TokenCryptoError, decrypt_token, encrypt_token
from app.settings import Settings


@dataclass(frozen=True)
class GmailTokens:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scope: str | None
    token_type: str | None


def get_gmail_tokens(db: Session, settings: Settings, account_id: int) -> GmailTokens | None:
    cred = (
        db.execute(
            select(OAuthCredential).where(
                OAuthCredential.provider == OAuthProvider.gmail,
                OAuthCredential.account_id == account_id,
            )
        )
        .scalars()
        .first()
    )
    if not cred:
        return None
    try:
        access = decrypt_token(settings, cred.access_token_enc)
        refresh = decrypt_token(settings, cred.refresh_token_enc) if cred.refresh_token_enc else None
    except TokenCryptoError:
        # Treat as disconnected if we can't decrypt.
        return None
    return GmailTokens(
        access_token=access,
        refresh_token=refresh,
        expires_at=cred.expires_at,
        scope=cred.scope,
        token_type=cred.token_type,
    )


def set_gmail_tokens(
    db: Session,
    settings: Settings,
    account_id: int,
    *,
    access_token: str,
    refresh_token: str | None,
    expires_at: datetime | None,
    scope: str | None,
    token_type: str | None,
) -> None:
    access_enc = encrypt_token(settings, access_token)
    refresh_enc = encrypt_token(settings, refresh_token) if refresh_token else None

    cred = (
        db.execute(
            select(OAuthCredential).where(
                OAuthCredential.provider == OAuthProvider.gmail,
                OAuthCredential.account_id == account_id,
            )
        )
        .scalars()
        .first()
    )
    if cred is None:
        cred = OAuthCredential(
            provider=OAuthProvider.gmail,
            account_id=account_id,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            expires_at=expires_at,
            scope=scope,
            token_type=token_type,
        )
        db.add(cred)
    else:
        cred.access_token_enc = access_enc
        if refresh_enc is not None:
            cred.refresh_token_enc = refresh_enc
        cred.expires_at = expires_at
        cred.scope = scope
        cred.token_type = token_type


def get_yahoo_app_password(db: Session, settings: Settings, account_id: int) -> str | None:
    cred = (
        db.execute(
            select(OAuthCredential).where(
                OAuthCredential.provider == OAuthProvider.yahoo,
                OAuthCredential.account_id == account_id,
            )
        )
        .scalars()
        .first()
    )
    if not cred:
        return None
    try:
        return decrypt_token(settings, cred.access_token_enc)
    except TokenCryptoError:
        return None

