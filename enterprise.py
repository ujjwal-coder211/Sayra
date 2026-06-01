"""Enterprise bridge - Saira (Sayra) se Aitotech-agents company ko command karna.

Sayra = Master Ujjwal ka personal Sovereign AGI / Chief of Staff.
Ye module Sayra ko Aitotech-agents (FastAPI backend) se jodta hai, taaki Sayra
business kaam company ke agents (research/strategy/dev/sales/delivery) ko
delegate kar sake aur results/leads wapas la sake.

Config (environment variables):
    ENTERPRISE_API_URL   - Aitotech-agents ka base URL (Railway), जैसे
                           https://aitotech-agents-production.up.railway.app
    ENTERPRISE_API_KEY   - (optional) shared secret, /webhooks/n8n ke liye

ENTERPRISE_API_URL set na ho to sab functions safely "not linked" batate hain
(koi crash nahi) — taaki Sayra akele bhi chalti rahe.
"""

from __future__ import annotations

import os

import requests

VALID_AGENTS = ("research", "strategy", "dev", "sales", "delivery")


def _base_url() -> str:
    return (os.environ.get("ENTERPRISE_API_URL", "") or "").rstrip("/")


def _api_key() -> str:
    return os.environ.get("ENTERPRISE_API_KEY", "") or ""


def is_configured() -> bool:
    return bool(_base_url())


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if _api_key():
        h["x-api-key"] = _api_key()
    return h


# ---------------------------------------------------------------------------
# Commands (Sayra -> company)
# ---------------------------------------------------------------------------
def create_task(title: str, agent_type: str, payload: dict | None = None, priority: int = 5) -> str:
    """Company ke kisi agent ko ek business task delegate karo."""
    if not is_configured():
        return "⚠️ Master, Aitotech enterprise abhi link nahi hai (ENTERPRISE_API_URL set karein)."
    if agent_type not in VALID_AGENTS:
        return f"⚠️ Unknown team: {agent_type}. Valid: {', '.join(VALID_AGENTS)}"
    try:
        res = requests.post(
            f"{_base_url()}/tasks",
            json={
                "title": title,
                "agent_type": agent_type,
                "payload": payload or {},
                "priority": priority,
            },
            headers=_headers(),
            timeout=20,
        )
        res.raise_for_status()
        data = res.json()
        return (
            f"✅ Master, maine '{agent_type}' team ko ye kaam saunp diya hai.\n"
            f"Task ID: {data.get('id', '?')}\n"
            f"Title: {title}\n"
            f"Orchestrator jald ise process karega — main result yaad rakhungi."
        )
    except Exception as exc:  # noqa: BLE001
        return f"❌ Task delegate nahi ho paya: {exc}"


def ask_agent(message: str, agent_type: str = "sales") -> str:
    """Company ke agent se turant (synchronous) jawaab lo — bina task banaye."""
    if not is_configured():
        return "⚠️ Enterprise link nahi hai."
    try:
        res = requests.post(
            f"{_base_url()}/public/chat",
            json={"message": message, "agent_type": agent_type},
            headers=_headers(),
            timeout=40,
        )
        res.raise_for_status()
        return res.json().get("answer", "(koi jawaab nahi)")
    except Exception as exc:  # noqa: BLE001
        return f"❌ Agent se baat nahi ho payi: {exc}"


# ---------------------------------------------------------------------------
# Reports (company -> Sayra)
# ---------------------------------------------------------------------------
def list_tasks(status: str | None = None, limit: int = 8) -> list[dict]:
    if not is_configured():
        return []
    try:
        url = f"{_base_url()}/tasks" + (f"?status={status}" if status else "")
        res = requests.get(url, headers=_headers(), timeout=20)
        res.raise_for_status()
        return res.json()[:limit]
    except Exception:  # noqa: BLE001
        return []


def get_leads(limit: int = 8) -> list[dict]:
    if not is_configured():
        return []
    try:
        res = requests.get(f"{_base_url()}/leads", headers=_headers(), timeout=20)
        res.raise_for_status()
        return res.json()[:limit]
    except Exception:  # noqa: BLE001
        return []


def format_status() -> str:
    """Company ki ek-line health + recent tasks ka summary (Master ke liye)।"""
    if not is_configured():
        return "⚠️ Master, Aitotech enterprise abhi link nahi hai."
    try:
        info = requests.get(f"{_base_url()}/", headers=_headers(), timeout=20).json()
    except Exception as exc:  # noqa: BLE001
        return f"❌ Company se connect nahi ho paya: {exc}"

    tasks = list_tasks(limit=5)
    lines = [
        "🏢 Aitotech Enterprise — status report:",
        f"  • Brain online: {info.get('name', 'API')} v{info.get('version', '?')}",
        f"  • Database: {'✅' if info.get('supabase_configured') else '❌'}"
        f" | LLM: {'✅' if info.get('llm_configured') else '❌'}"
        f" | Actions(n8n): {'✅' if info.get('n8n_configured') else '❌'}",
        f"  • Teams: {', '.join(info.get('agents', []))}",
    ]
    if tasks:
        lines.append("  • Recent tasks:")
        for t in tasks:
            lines.append(f"     - [{t.get('status')}] {t.get('title')} ({t.get('agent_type')})")
    else:
        lines.append("  • Abhi koi task nahi.")
    return "\n".join(lines)


def format_leads() -> str:
    if not is_configured():
        return "⚠️ Enterprise link nahi hai."
    leads = get_leads()
    if not leads:
        return "📭 Master, abhi koi naya lead nahi hai."
    lines = ["📥 Website se aaye leads:"]
    for l in leads:
        who = l.get("name") or l.get("email") or "Unknown"
        lines.append(f"  • {who} [{l.get('status')}] — {l.get('source')}"
                     + (f" / {l.get('service_slug')}" if l.get("service_slug") else ""))
    return "\n".join(lines)


def short_status() -> str:
    """system_prompt me daalne ke liye ek choti line."""
    if not is_configured():
        return "Enterprise: not linked"
    pending = len([t for t in list_tasks(limit=50) if t.get("status") == "pending"])
    leads = len(get_leads(limit=50))
    return f"Aitotech enterprise: LINKED | pending tasks: {pending} | leads: {leads}"
