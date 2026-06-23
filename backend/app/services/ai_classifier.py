from __future__ import annotations

import json
import time

import httpx

from app.db.models import CUSTOM_LABELS

# ---------------------------------------------------------------------------
# Gemini free-tier endpoint (gemini-2.0-flash — 1,500 RPD, no credit card)
# ---------------------------------------------------------------------------

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)
_OPENAI_URL = "https://api.openai.com/v1/chat/completions"

_SYSTEM_PROMPT = (
    "You classify email senders into inbox organization labels. "
    "Respond with JSON only — no explanation, no markdown.\n\n"
    f"Available labels: {json.dumps(CUSTOM_LABELS)}\n\n"
    "Rules:\n"
    "- Choose 1 to 3 labels that best fit the sender.\n"
    "- Base your decision on the sender display name, domain, and sample subjects.\n"
    "- If nothing fits confidently, return an empty labels list.\n"
    'Response schema: {"labels": [<label>, ...]}'
)


class AIClassifierError(Exception):
    pass


def classify_sender_gemini(
    *,
    api_key: str,
    sender_email: str,
    sender_name: str | None,
    sample_subjects: list[str],
) -> list[str]:
    """
    Ask Gemini to classify a single sender. Returns a list of label strings.
    Raises AIClassifierError on network or API failure.
    """
    display = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    subjects_text = "\n".join(f"  - {s}" for s in sample_subjects[:5]) or "  (none)"
    user_message = (
        f"Sender: {display}\n"
        f"Sample subjects:\n{subjects_text}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{_SYSTEM_PROMPT}\n\n{user_message}"}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
            "maxOutputTokens": 64,
        },
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                _GEMINI_URL,
                params={"key": api_key},
                json=payload,
            )
        if res.status_code == 429:
            raise AIClassifierError("Gemini rate limit reached — try again later.")
        if res.status_code >= 400:
            raise AIClassifierError(f"Gemini API error {res.status_code}: {res.text[:200]}")

        data = res.json()
        raw_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return _parse_label_response(raw_text)

    except AIClassifierError:
        raise
    except Exception as e:
        raise AIClassifierError(f"Gemini request failed: {e}") from e


def classify_sender_openai(
    *,
    api_key: str,
    sender_email: str,
    sender_name: str | None,
    sample_subjects: list[str],
) -> list[str]:
    """
    Ask OpenAI to classify a single sender. Returns a list of label strings.
    """
    display = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    subjects_text = "\n".join(f"  - {s}" for s in sample_subjects[:5]) or "  (none)"
    user_message = (
        f"Sender: {display}\n"
        f"Sample subjects:\n{subjects_text}"
    )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 64,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                _OPENAI_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
        if res.status_code == 429:
            raise AIClassifierError("OpenAI rate limit reached — try again later.")
        if res.status_code >= 400:
            raise AIClassifierError(f"OpenAI API error {res.status_code}: {res.text[:200]}")

        data = res.json()
        raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _parse_label_response(raw_text)

    except AIClassifierError:
        raise
    except Exception as e:
        raise AIClassifierError(f"OpenAI request failed: {e}") from e


def _parse_label_response(raw: str) -> list[str]:
    """Parse AI JSON response and validate label names."""
    try:
        parsed = json.loads(raw.strip())
        labels = parsed.get("labels", [])
        if not isinstance(labels, list):
            return []
        return [l for l in labels if isinstance(l, str) and l in CUSTOM_LABELS][:3]
    except (json.JSONDecodeError, AttributeError):
        return []


def classify_sender(
    *,
    provider: str,
    api_key: str,
    sender_email: str,
    sender_name: str | None,
    sample_subjects: list[str],
) -> list[str]:
    """Dispatch to the right provider."""
    if provider == "gemini":
        return classify_sender_gemini(
            api_key=api_key,
            sender_email=sender_email,
            sender_name=sender_name,
            sample_subjects=sample_subjects,
        )
    if provider == "openai":
        return classify_sender_openai(
            api_key=api_key,
            sender_email=sender_email,
            sender_name=sender_name,
            sample_subjects=sample_subjects,
        )
    raise AIClassifierError(f"Unknown AI provider: {provider!r}. Use 'gemini' or 'openai'.")
