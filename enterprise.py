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

VALID_AGENTS = (
    "research",
    "opportunity",
    "strategy",
    "product",
    "dev",
    "marketing",
    "sales",
    "delivery",
    "finance",
    "support",
)


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


def _get(path: str, timeout: int = 20):
    """GET helper — error par None/[] safely."""
    if not is_configured():
        return None
    try:
        res = requests.get(f"{_base_url()}{path}", headers=_headers(), timeout=timeout)
        res.raise_for_status()
        return res.json()
    except Exception:  # noqa: BLE001
        return None


def _post(path: str, body: dict, timeout: int = 30):
    if not is_configured():
        return None
    try:
        res = requests.post(
            f"{_base_url()}{path}", json=body, headers=_headers(), timeout=timeout
        )
        res.raise_for_status()
        return res.json()
    except Exception:  # noqa: BLE001
        return None


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
    advice = len(list_advice(limit=50))
    return (
        f"Aitotech enterprise: LINKED | pending tasks: {pending} | "
        f"leads: {leads} | advice needed: {advice}"
    )


# ---------------------------------------------------------------------------
# Command Center (workflow + profit + human-in-the-loop) — dashboard ke liye
# ---------------------------------------------------------------------------
def get_pipelines(limit: int = 10) -> list[dict]:
    """Workflow timeline — tasks grouped by pipeline."""
    data = _get("/pipelines") or []
    return data[:limit] if isinstance(data, list) else []


def get_finance() -> dict:
    """Profit summary (projected + actual)."""
    return _get("/finance/summary") or {}


def get_opportunities(limit: int = 10) -> list[dict]:
    """Opportunity agent ke paisa-banane wale findings."""
    data = _get("/opportunities") or []
    return data[:limit] if isinstance(data, list) else []


def get_deals(limit: int = 10) -> list[dict]:
    data = _get("/deals") or []
    return data[:limit] if isinstance(data, list) else []


def list_advice(status: str = "pending", limit: int = 20) -> list[dict]:
    """Sayra ke advice requests — jahan Master ki zaroorat hai."""
    data = _get(f"/advice?status={status}") or []
    return data[:limit] if isinstance(data, list) else []


def answer_advice(advice_id: str, decision: str, response: str = "") -> dict:
    """Master ki advice agents tak bhejo (human -> agents)."""
    res = _post(
        f"/advice/{advice_id}/answer",
        {"decision": decision, "response": response},
    )
    return res or {"ok": False, "message": "Advice bhejne me dikkat (enterprise link check karein)."}


def start_pipeline(
    title: str,
    market: str | None = None,
    region: str | None = None,
    notes: str | None = None,
) -> dict:
    """Pura autonomous pipeline (research -> ... -> sales) shuru karo."""
    res = _post(
        "/pipeline",
        {
            "title": title,
            "start_agent": "research",
            "market": market,
            "region": region,
            "notes": notes,
            "priority": 7,
        },
    )
    return res or {"ok": False, "message": "Pipeline start nahi hua (enterprise link check karein)."}


def run_tick() -> dict:
    """Orchestrator ko ek batch chalao."""
    return _post("/orchestrator/tick", {}) or {"processed": 0}


def _money(n, currency: str = "INR") -> str:
    try:
        return f"₹{float(n or 0):,.0f}" if currency == "INR" else f"{float(n or 0):,.0f} {currency}"
    except (TypeError, ValueError):
        return str(n)


def format_finance() -> str:
    """Profit summary chat me dikhane ke liye (Master ko)।"""
    if not is_configured():
        return "⚠️ Master, Aitotech enterprise abhi link nahi hai."
    f = get_finance()
    if not f:
        return "📊 Master, abhi profit data nahi mila (deals add karein)."
    cur = f.get("currency", "INR")
    return "\n".join(
        [
            "💰 Aitotech — profit report:",
            f"  • Projected profit: {_money(f.get('projected_profit'), cur)}",
            f"  • Actual profit: {_money(f.get('actual_profit'), cur)}",
            f"  • Actual revenue: {_money(f.get('actual_revenue'), cur)}",
            f"  • Deals: {f.get('deal_count', 0)} (won: {f.get('won_count', 0)})",
        ]
    )


def format_opportunities() -> str:
    if not is_configured():
        return "⚠️ Enterprise link nahi hai."
    opps = get_opportunities()
    if not opps:
        return "🔍 Master, abhi koi opportunity nahi. Ek pipeline shuru karwaun?"
    lines = ["🎯 Paisa-banane wali opportunities:"]
    for o in opps:
        lines.append(f"  • [{o.get('status')}] {o.get('title')}")
    return "\n".join(lines)


def format_advice() -> str:
    if not is_configured():
        return "⚠️ Enterprise link nahi hai."
    adv = list_advice()
    if not adv:
        return "✅ Master, abhi aapki kahin zaroorat nahi — sab smooth chal raha hai."
    lines = ["💬 Master, in par aapki advice chahiye:"]
    for a in adv:
        lines.append(f"  • {a.get('question')}")
    lines.append("(Dashboard → COMPANY tab se approve/reject kar sakte ho.)")
    return "\n".join(lines)


def orchestrator_status() -> dict:
    """Company auto-run (running mode) status backend se."""
    return _get("/orchestrator/status") or {}


def get_overview() -> dict:
    """Dashboard Command Center ke liye sab ek saath + health status."""
    info = _get("/") or {}
    online = bool(info)
    db_ok = bool(info.get("supabase_configured"))
    orch = orchestrator_status()
    running = bool(orch.get("running"))

    if not is_configured():
        state, label = "unlinked", "NOT LINKED"
    elif not online:
        state, label = "offline", "BACKEND OFFLINE"
    elif not db_ok:
        state, label = "db_error", "DATABASE ERROR"
    elif running:
        state, label = "running", "RUNNING"
    else:
        state, label = "idle", "IDLE"

    return {
        "linked": is_configured(),
        "online": online,
        "db_ok": db_ok,
        "running": running,
        "state": state,
        "state_label": label,
        "health": {
            "db": db_ok,
            "llm": bool(info.get("llm_configured")),
            "n8n": bool(info.get("n8n_configured")),
        },
        "info": info,
        "finance": get_finance(),
        "pipelines": get_pipelines(limit=8),
        "advice": list_advice(limit=20),
        "opportunities": get_opportunities(limit=6),
        "leads": get_leads(limit=8),
        "deals": get_deals(limit=6),
    }
