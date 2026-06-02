"""Groq API key validation + live connection test."""

from __future__ import annotations

import os
from typing import Any

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[misc, assignment]

PLACEHOLDER_KEYS = frozenset(
    {
        "",
        "gsk_your_default_here",
        "your-groq-api-key",
        "gsk_xxxxxxxxxxxxxxxx",
    }
)


def get_groq_api_key() -> str | None:
    raw = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not raw or raw in PLACEHOLDER_KEYS:
        return None
    if not raw.startswith("gsk_"):
        return None
    return raw


def groq_client() -> Groq | None:
    key = get_groq_api_key()
    if not key or Groq is None:
        return None
    return Groq(api_key=key)


def groq_config_status() -> dict[str, Any]:
    key = get_groq_api_key()
    return {
        "configured": key is not None,
        "key_prefix": (key[:8] + "…") if key else None,
        "model": os.environ.get("SAIRA_MODEL", "llama-3.3-70b-versatile"),
        "fallback_model": os.environ.get("SAIRA_FALLBACK_MODEL", "llama-3.1-8b-instant"),
    }


def test_groq_connection() -> dict[str, Any]:
    """Minimal live call — status page / health ke liye."""
    cfg = groq_config_status()
    if not cfg["configured"]:
        return {
            **cfg,
            "connected": False,
            "error": "GROQ_API_KEY Railway Variables me set nahi hai (ya galat placeholder hai).",
        }

    client = groq_client()
    if client is None:
        return {**cfg, "connected": False, "error": "Groq SDK load nahi hua."}

    model = os.environ.get("SAIRA_FALLBACK_MODEL", "llama-3.1-8b-instant")
    try:
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=5,
            temperature=0,
        )
        text = (res.choices[0].message.content or "").strip()
        return {**cfg, "connected": True, "test_model": model, "test_reply": text[:20]}
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        hint = ""
        if "401" in err or "invalid" in err.lower() or "api key" in err.lower():
            hint = " API key galat/expired — console.groq.com se nayi key banao."
        elif "model" in err.lower():
            hint = f" Model '{model}' available nahi — SAIRA_MODEL env badlo."
        return {**cfg, "connected": False, "error": err + hint, "test_model": model}
