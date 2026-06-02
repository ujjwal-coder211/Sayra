"""Speech STT/TTS — Groq Whisper + optional gTTS fallback."""

from __future__ import annotations

import io
import os
import re
import tempfile
from typing import Any

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[misc, assignment]

try:
    from gtts import gTTS
except ImportError:
    gTTS = None  # type: ignore[misc, assignment]


import groq_config


WHISPER_MODEL = os.environ.get("SAIRA_WHISPER_MODEL", "whisper-large-v3-turbo")


def _groq_client() -> Groq | None:
    return groq_config.groq_client()


def transcribe_file(file_storage, language: str | None = None) -> tuple[str | None, str | None]:
    """Upload audio file -> text via Groq Whisper."""
    client = _groq_client()
    if client is None:
        return None, "Groq API not configured"

    suffix = ".webm"
    name = (file_storage.filename or "").lower()
    if name.endswith(".mp4") or name.endswith(".m4a"):
        suffix = ".mp4"
    elif name.endswith(".wav"):
        suffix = ".wav"
    elif name.endswith(".ogg"):
        suffix = ".ogg"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_storage.save(tmp.name)
            tmp_path = tmp.name

        kwargs: dict[str, Any] = {"model": WHISPER_MODEL}
        if language:
            kwargs["language"] = language

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(file=audio_file, **kwargs)

        text = (getattr(result, "text", None) or "").strip()
        return text or None, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _clean_for_speech(text: str) -> str:
    """Markdown/noise hatao — TTS ke liye."""
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    t = re.sub(r"_([^_]+)_", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"#{1,6}\s*", "", t)
    return t.strip()[:2000]


def synthesize_mp3(text: str, lang: str = "hi") -> tuple[bytes | None, str | None]:
    """Text -> MP3 bytes (gTTS). Works on devices where browser TTS fails."""
    if gTTS is None:
        return None, "gTTS not installed"
    clean = _clean_for_speech(text)
    if not clean:
        return None, "Empty text"
    try:
        buf = io.BytesIO()
        # Hindi fail ho to English try
        for code in (lang, "en"):
            try:
                gTTS(text=clean, lang=code).write_to_fp(buf)
                buf.seek(0)
                return buf.read(), None
            except Exception:
                buf = io.BytesIO()
                continue
        return None, "TTS language failed"
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def speech_capabilities() -> dict[str, Any]:
    return {
        "whisper": _groq_client() is not None,
        "whisper_model": WHISPER_MODEL,
        "server_tts": gTTS is not None,
    }
