from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.settings import Settings


class TokenCryptoError(Exception):
    pass


def _fernet(settings: Settings) -> Fernet:
    if not settings.token_encryption_key:
        raise TokenCryptoError("MAILMIND_TOKEN_ENCRYPTION_KEY is required to store tokens")
    try:
        return Fernet(settings.token_encryption_key.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise TokenCryptoError(f"Invalid MAILMIND_TOKEN_ENCRYPTION_KEY: {e}") from e


def encrypt_token(settings: Settings, token: str) -> str:
    f = _fernet(settings)
    return f.encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(settings: Settings, token_enc: str) -> str:
    f = _fernet(settings)
    try:
        return f.decrypt(token_enc.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise TokenCryptoError("Failed to decrypt token (wrong key?)") from e

