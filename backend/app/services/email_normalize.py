from __future__ import annotations


def normalize_sender_email(*, provider: str, sender_email: str) -> str:
    """
    Best-effort normalization for grouping/insights.

    Goals:
    - Avoid casing/whitespace fragmentation.
    - For Gmail addresses, collapse plus-aliasing (local+tag@gmail.com -> local@gmail.com).
    """
    e = (sender_email or "").strip().lower()
    if not e or "@" not in e:
        return ""

    local, domain = e.split("@", 1)
    local = local.strip()
    domain = domain.strip()
    if not local or not domain:
        return ""

    # Gmail: plus aliases are not a distinct mailbox identity.
    if provider == "gmail" and domain in {"gmail.com", "googlemail.com"}:
        local = local.split("+", 1)[0]

    return f"{local}@{domain}"

