"""Thin REST client for the Gemini API (text + text-to-speech). No SDK: fewer moving parts."""

from __future__ import annotations

import base64
import time
import wave
from pathlib import Path
from typing import Any

import requests

from pipeline.common import check_http, env, with_retries

BASE = "https://generativelanguage.googleapis.com/v1beta"


def _post(model: str, body: dict[str, Any], timeout: int = 180) -> tuple[dict[str, Any], float]:
    url = f"{BASE}/models/{model}:generateContent"
    headers = {"x-goog-api-key": env("GEMINI_API_KEY"), "Content-Type": "application/json"}

    def call() -> tuple[dict[str, Any], float]:
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        except requests.RequestException as exc:  # network blips are worth a retry
            from pipeline.common import Retryable

            raise Retryable(str(exc)) from exc
        check_http(resp)
        return resp.json(), time.perf_counter() - t0

    return with_retries(call, label=model)


def list_models() -> list[dict[str, Any]]:
    resp = requests.get(f"{BASE}/models", headers={"x-goog-api-key": env("GEMINI_API_KEY")}, params={"pageSize": 200}, timeout=30)
    check_http(resp)
    return resp.json().get("models", [])


def generate_text(prompt: str, *, model: str, json_mode: bool = False, temperature: float = 0.7) -> tuple[str, float, dict[str, Any]]:
    config: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        config["responseMimeType"] = "application/json"
    data, latency = _post(model, {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config})
    text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    return text, latency, data.get("usageMetadata", {})


def tts(text: str, *, model: str, voice: str, style: str, out: Path) -> tuple[float, dict[str, Any]]:
    """Speak `text` with a prebuilt voice and a plain-language style instruction; writes a 24 kHz mono WAV."""
    prompt = f"{style}:\n{text}" if style else text
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }
    data, latency = _post(model, body)
    part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
    pcm = base64.b64decode(part["data"])
    rate = 24000
    mime = part.get("mimeType", "")
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return latency, data.get("usageMetadata", {})
