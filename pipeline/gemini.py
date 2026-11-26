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
    # Keep the prompt to "<one short direction>: <text>". A long instruction block was read aloud word for word
    # instead of the Arabic (FAILURES.md F6); anything in the prompt may be spoken. narration.py rejects takes that
    # are far longer than the text, which catches both read-aloud instructions and invented sentences.
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
    audio = base64.b64decode(part["data"])
    rate = 24000
    mime = part.get("mimeType", "")
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    write_wav(audio, rate, out)
    return latency, data.get("usageMetadata", {})


def write_wav(audio: bytes, rate: int, out: Path) -> None:
    """Older TTS models return raw 16-bit PCM; gemini-3.8-flash-tts returns a complete WAV file (RIFF header + data +
    a trailing metadata chunk). Wrapping that in another header made every line start with a click and end with a
    0.16 s full-scale buzz (FAILURES.md F11). So: if it is already a WAV, read only its audio frames."""
    import io

    channels, width = 1, 2
    if audio[:4] == b"RIFF":
        with wave.open(io.BytesIO(audio)) as inner:
            channels, width, rate = inner.getnchannels(), inner.getsampwidth(), inner.getframerate()
            audio = inner.readframes(inner.getnframes())
    with wave.open(str(out), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(audio)


def repair_nested_wav(path: Path) -> bool:
    """Fix a file written before the F11 fix (a WAV inside a WAV) in place, without calling the API again."""
    with wave.open(str(path)) as outer:
        rate, frames = outer.getframerate(), outer.readframes(outer.getnframes())
    if frames[:4] != b"RIFF":
        return False
    write_wav(frames, rate, path)
    return True
