"""
AI-powered sender category suggestions.
Uses OpenAI when OPENAI_API_KEY is set, otherwise rule-based keyword matching.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

MAIN_CATEGORIES = [
    "Essentials",
    "Life",
    "Software/Tech",
    "Work",
    "Social",
    "Other",
]

# Keyword hints for rule-based suggestion (domain or sender name)
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Essentials": [
        "insurance", "bank", "paypal", "stripe", "utility", "utilities",
        "electric", "gas", "water", "rent", "mortgage", "government",
        "irs", "dmv", "ssa", "usps", "fedex", "ups", "delivery",
    ],
    "Life": [
        "amazon", "ebay", "etsy", "walmart", "target", "doordash", "ubereats",
        "grubhub", "instacart", "uber", "lyft", "airbnb", "booking",
        "entertainment", "netflix", "spotify", "hulu", "disney",
    ],
    "Software/Tech": [
        "github", "gitlab", "bitbucket", "aws", "google", "microsoft",
        "azure", "cloud", "digitalocean", "heroku", "vercel", "netlify",
        "godaddy", "namecheap", "npm", "pypi", "stackoverflow",
        "notion", "slack", "atlassian", "jira", "linear",
    ],
    "Work": [
        "linkedin", "indeed", "glassdoor", "company", "hr@", "careers",
        "invoice", "contract", "legal", "accounting", "payroll",
    ],
    "Social": [
        "facebook", "twitter", "x.com", "instagram", "tiktok", "reddit",
        "pinterest", "tumblr", "meetup", "discord", "whatsapp", "telegram",
    ],
}


def _normalize(s: str) -> str:
    return (s or "").lower().strip()


def _domain(email: str) -> str:
    if "@" in email:
        return _normalize(email.split("@", 1)[1])
    return ""


def rule_based_suggest(sender_email: str, sender_name: Optional[str] = None) -> Dict[str, Any]:
    """Suggest category and optional subcategory using keyword rules."""
    domain = _domain(sender_email)
    name = _normalize(sender_name or "")
    combined = f"{domain} {name}"

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in combined or kw in domain or kw in name:
                return {
                    "suggested_category": category,
                    "suggested_subcategory": None,
                }
    return {"suggested_category": "Other", "suggested_subcategory": None}


def suggest_with_openai(senders: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Use OpenAI to suggest categories. Returns None if not configured or on error."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("openai package not installed; use pip install openai for AI suggestions")
        return None

    # Build list of sender lines for the prompt
    lines = []
    for i, s in enumerate(senders[:100]):  # cap at 100
        email = s.get("email", "")
        name = s.get("name") or email.split("@")[0] if email else ""
        lines.append(f"{i + 1}. {name} <{email}>")

    prompt = f"""Classify each of these email senders into exactly one main category. Reply with one line per sender: "number. Category" or "number. Category / Subcategory".

Senders:
{chr(10).join(lines)}

Categories (use exactly these): Essentials, Life, Software/Tech, Work, Social, Other.
- Essentials: insurance, bank, utilities, government, rent, delivery
- Life: shopping, food delivery, travel, entertainment
- Software/Tech: GitHub, cloud, dev tools, domain registrars
- Work: company, HR, clients, invoices
- Social: social networks, dating, community
- Other: anything else

Reply only with the numbered list, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = (response.choices[0].message.content or "").strip()
    except Exception as e:
        logger.exception("OpenAI suggest failed: %s", e)
        return None

    # Parse "1. Category" or "1. Category / Subcategory"
    results = []
    sender_list = senders[:100]
    pattern = re.compile(r"(\d+)\.\s*([^/\n]+)(?:\s*/\s*([^\n]+))?")
    for m in pattern.finditer(text):
        idx = int(m.group(1))
        if 1 <= idx <= len(sender_list):
            cat = m.group(2).strip()
            sub = m.group(3).strip() if m.group(3) else None
            if cat not in MAIN_CATEGORIES:
                cat = "Other"
            results.append({
                "index": idx - 1,
                "suggested_category": cat,
                "suggested_subcategory": sub,
            })
    if len(results) != len(sender_list):
        return None
    return results


def suggest_categories(senders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Suggest categories for a list of senders.
    Returns { "suggestions": [ { sender_email, sender_name, suggested_category, suggested_subcategory } ], "provider": "openai"|"rules" }.
    """
    # Try OpenAI first if we have enough senders to make it worthwhile (e.g. 5+)
    provider = "rules"
    openai_results = None
    if len(senders) >= 3:
        openai_results = suggest_with_openai(senders)

    if openai_results is not None:
        provider = "openai"
        suggestions = []
        for i, s in enumerate(senders[:100]):
            if i < len(openai_results):
                r = openai_results[i]
                suggestions.append({
                    "sender_email": s.get("email", ""),
                    "sender_name": s.get("name"),
                    "suggested_category": r.get("suggested_category", "Other"),
                    "suggested_subcategory": r.get("suggested_subcategory"),
                })
            else:
                suggestions.append({
                    "sender_email": s.get("email", ""),
                    "sender_name": s.get("name"),
                    "suggested_category": "Other",
                    "suggested_subcategory": None,
                })
        return {"suggestions": suggestions, "provider": provider}
    # Rule-based fallback
    suggestions = []
    for s in senders:
        email = s.get("email", "")
        name = s.get("name")
        r = rule_based_suggest(email, name)
        suggestions.append({
            "sender_email": email,
            "sender_name": name,
            "suggested_category": r["suggested_category"],
            "suggested_subcategory": r.get("suggested_subcategory"),
        })
    return {"suggestions": suggestions, "provider": provider}
