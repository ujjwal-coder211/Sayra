"""Sovereign Brain — Groq ke saath fallback + learning cache.

Jab Groq respond na kare ya rate limit hit ho, Sayra yahan se jawab deti hai:
  1. Groq primary model (retry on 429)
  2. Groq fallback model (chhota / alag quota)
  3. Ollama local model (optional, SAIRA_OLLAMA_URL)
  4. Cached past Groq answers (similar query — "cloned" knowledge)
  5. Aitotech enterprise agents (business queries)
  6. Sovereign local mode (memory + rules + web scrape hint)

Har successful cloud answer cache me save hota hai — time ke saath Sayra
apni knowledge base build karti hai (Groq se seekh kar).
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any

import requests

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[misc, assignment]

import enterprise


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9\u0900-\u097f]+", text.lower()) if len(w) > 2}


def _similarity(a: str, b: str) -> float:
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


class SovereignBrain:
    CACHE_FILE = "sovereign_cache.json"
    MAX_CACHE = 500
    CACHE_HIT_THRESHOLD = 0.45

    def __init__(self, data_root: str, groq_api_key: str | None) -> None:
        self.data_root = data_root
        self.cache_path = os.path.join(data_root, "Saira_Sovereign_OS", self.CACHE_FILE)
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

        self.primary_model = os.environ.get("SAIRA_MODEL", "llama-3.3-70b-versatile")
        self.fallback_model = os.environ.get(
            "SAIRA_FALLBACK_MODEL", "llama-3.1-8b-instant"
        )
        # Ollama sirf tab jab explicitly enable ho — GPU-less PC pe system atak jata hai
        ollama_flag = (os.environ.get("SAIRA_OLLAMA_ENABLED") or "").lower()
        self.ollama_enabled = ollama_flag in ("1", "true", "yes", "on")
        self.ollama_url = (os.environ.get("SAIRA_OLLAMA_URL") or "").rstrip("/")
        self.ollama_model = os.environ.get("SAIRA_OLLAMA_MODEL", "qwen2.5:0.5b")

        self.groq_client = None
        if groq_api_key and Groq is not None:
            self.groq_client = Groq(api_key=groq_api_key)

        self.cache: list[dict[str, Any]] = self._load_cache()
        self.last_source = "none"
        self.last_error: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(
        self,
        messages: list[dict[str, str]],
        user_query: str = "",
        learn: bool = True,
    ) -> tuple[str, str]:
        """Return (answer_text, source_label)."""
        self.last_error = None
        query = user_query or self._extract_user(messages)

        # 1–2. Groq primary + fallback
        for label, model in (
            ("groq", self.primary_model),
            ("groq-fallback", self.fallback_model),
        ):
            if model == self.primary_model and label == "groq-fallback":
                continue  # same model skip
            ans = self._try_groq(messages, model)
            if ans:
                self.last_source = label
                if learn:
                    self._remember(query, ans, label)
                return ans, label

        # 3. Ollama (local clone — apna model)
        ans = self._try_ollama(messages)
        if ans:
            self.last_source = "ollama"
            if learn:
                self._remember(query, ans, "ollama")
            return ans, "ollama"

        # 4. Cached knowledge (Groq se pehle seekhi hui)
        ans = self._try_cache(query)
        if ans:
            self.last_source = "cache"
            return ans, "cache"

        # 5. Enterprise agents (business backup)
        ans = self._try_enterprise(query)
        if ans:
            self.last_source = "enterprise"
            return ans, "enterprise"

        # 6. Sovereign local (rules + memory hint passed in messages)
        ans = self._sovereign_local(query, messages)
        self.last_source = "sovereign"
        return ans, "sovereign"

    def status(self) -> dict[str, Any]:
        return {
            "groq": bool(self.groq_client),
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "ollama": bool(self.ollama_url and self.ollama_enabled),
            "ollama_enabled": self.ollama_enabled,
            "ollama_model": self.ollama_model if self.ollama_url else None,
            "enterprise": enterprise.is_configured(),
            "cache_entries": len(self.cache),
            "last_source": self.last_source,
            "last_error": self.last_error,
        }

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------
    def _try_groq(self, messages: list[dict[str, str]], model: str) -> str | None:
        if not self.groq_client:
            return None
        for attempt in range(3):
            try:
                res = self.groq_client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=0.7,
                    max_tokens=2048,
                )
                text = (res.choices[0].message.content or "").strip()
                return text or None
            except Exception as exc:  # noqa: BLE001
                err = str(exc).lower()
                self.last_error = str(exc)
                if "429" in err or "rate" in err or "limit" in err:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                if attempt == 0 and model == self.primary_model:
                    continue
                break
        return None

    def _try_ollama(self, messages: list[dict[str, str]]) -> str | None:
        if not self.ollama_url or not self.ollama_enabled:
            return None
        try:
            # CPU-only PC: chhota context + kam tokens taaki system na atke
            res = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,
                        "num_predict": 256,
                        "num_thread": int(os.environ.get("SAIRA_OLLAMA_THREADS", "2")),
                    },
                },
                timeout=int(os.environ.get("SAIRA_OLLAMA_TIMEOUT", "45")),
            )
            res.raise_for_status()
            text = (res.json().get("message") or {}).get("content", "").strip()
            return text or None
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            return None

    def _try_cache(self, query: str) -> str | None:
        if not query or not self.cache:
            return None
        best_score = 0.0
        best_answer = None
        for entry in reversed(self.cache):
            score = _similarity(query, entry.get("query", ""))
            if score > best_score:
                best_score = score
                best_answer = entry.get("response")
        if best_score >= self.CACHE_HIT_THRESHOLD and best_answer:
            return f"{best_answer}\n\n_[Sovereign cache — similarity {best_score:.0%}]_"
        return None

    def _try_enterprise(self, query: str) -> str | None:
        if not enterprise.is_configured() or len(query.strip()) < 4:
            return None
        q = query.lower()
        agent = "sales"
        if any(k in q for k in ["research", "market", "competitor", "रिसर्च"]):
            agent = "research"
        elif any(k in q for k in ["strategy", "plan", "रणनीति"]):
            agent = "strategy"
        elif any(k in q for k in ["code", "dev", "build", "कोड"]):
            agent = "dev"
        elif any(k in q for k in ["deliver", "client", "delivery"]):
            agent = "delivery"
        try:
            ans = enterprise.ask_agent(query, agent_type=agent)
            if ans and not ans.startswith("❌") and not ans.startswith("⚠️"):
                return ans
        except Exception:  # noqa: BLE001
            pass
        return None

    def _sovereign_local(self, query: str, messages: list[dict[str, str]]) -> str:
        """Last resort — no cloud LLM. Memory + fixed handlers."""
        q = query.lower().strip()
        ctx = ""
        for m in messages:
            if m.get("role") == "system":
                ctx = m.get("content", "")
                break

        if any(w in q for w in ["hello", "hi", "namaste", "hey", "master"]):
            return (
                "Master, main Sovereign mode me hoon — Groq abhi reachable nahi hai, "
                "par main online hoon. Apna kaam bataiye; enterprise bridge ya cache se "
                "jitna ho sake help karungi."
            )
        if any(w in q for w in ["status", "health", "system", "stats"]):
            if "Hardware:" in ctx:
                snippet = ctx.split("Hardware:")[1].split("\n")[0].strip()
                return f"Master, Sovereign status: {snippet}. Cloud LLM abhi offline/limit pe hai."
            return "Master, system monitor active hai. Groq link restore hone ka wait kar rahi hoon."

        if any(w in q for w in ["help", "kya kar", "commands", "madad"]):
            return (
                "Master, abhi Sovereign (offline) mode:\n"
                "• 'company status' / 'leads' — enterprise report\n"
                "• 'delegate research …' — team ko task\n"
                "• Groq wapas aate hi full intelligence restore ho jayegi\n"
                "• Pehle ke jawab cache se mil sakte hain — wahi sawal dubara poochhiye"
            )

        # Memory hint from system prompt
        if "Relevant memory:" in ctx:
            mem = ctx.split("Relevant memory:")[1].split("Instructions:")[0].strip()
            if mem and len(mem) > 20:
                return (
                    f"Master, Groq abhi unavailable hai. Meri yaad se related yeh mila:\n\n{mem}\n\n"
                    "Poora fresh jawab ke liye thodi der baad dubara try karein."
                )

        return (
            "Master, abhi cloud neural link (Groq) respond nahi kar raha — rate limit ya outage ho sakta hai. "
            "Main Sovereign mode me hoon: enterprise commands ('leads', 'company status', 'delegate …') "
            "ab bhi chalenge. Groq restore hone par main full intelligence ke saath wapas aaungi."
        )

    # ------------------------------------------------------------------
    # Learning cache ("clone" Groq answers over time)
    # ------------------------------------------------------------------
    def _remember(self, query: str, response: str, source: str) -> None:
        if not query or not response or len(response) < 10:
            return
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:500],
            "response": response[:4000],
            "source": source,
        }
        self.cache.append(entry)
        if len(self.cache) > self.MAX_CACHE:
            self.cache = self.cache[-self.MAX_CACHE :]
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _load_cache(self) -> list[dict[str, Any]]:
        if not os.path.exists(self.cache_path):
            return []
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def _extract_user(messages: list[dict[str, str]]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return m.get("content", "")
        return ""
