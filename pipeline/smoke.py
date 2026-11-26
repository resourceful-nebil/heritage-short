"""Smoke test: call each provider once, log latency to runs.jsonl, and print which models the keys can use."""

from __future__ import annotations

import time

from pipeline import gemini, keyframes
from pipeline.common import OUT, env, log_call, out_path, run_ffmpeg


def run() -> None:
    ok = True
    print("[1/4] Gemini: models visible to this key")
    try:
        names = [m["name"].removeprefix("models/") for m in gemini.list_models()]
        print("   text:", ", ".join(n for n in names if "flash" in n and "tts" not in n and "image" not in n)[:400])
        print("   tts :", ", ".join(n for n in names if "tts" in n) or "(none found)")
    except Exception as exc:
        ok = False
        print("   FAILED:", exc)

    print("[2/4] Gemini text")
    model = env("GEMINI_TEXT_MODEL", "gemini-2.5-flash", required=False)
    try:
        text, latency, usage = gemini.generate_text("Reply with the single word: ready", model=model)
        log_call("smoke", model, params={"usage": usage}, latency_s=latency)
        print(f"   {model}: {text.strip()!r} in {latency:.2f}s")
    except Exception as exc:
        ok = False
        print("   FAILED:", exc)

    print("[3/4] Gemini TTS (Arabic)")
    tts_model = env("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts", required=False)
    wav = out_path("smoke", "tts", "check", "wav")
    try:
        latency, usage = gemini.tts("مرحبا، هذا اختبار قصير للصوت.", model=tts_model, voice="Charon", style="Say warmly and slowly", out=wav)
        log_call("smoke", tts_model, params={"voice": "Charon", "usage": usage}, latency_s=latency, output=wav)
        print(f"   {tts_model}: wrote {wav.name} in {latency:.2f}s")
    except Exception as exc:
        ok = False
        print("   FAILED:", exc)

    print("[4/4] Cloudflare FLUX + FFmpeg")
    img = out_path("smoke", "flux", "check", "jpg")
    try:
        data, latency, params = keyframes._generate("a clay coffee pot on a woven mat, soft morning light, illustration", seed=1, steps=4)
        img.write_bytes(data)
        log_call("smoke", env("CLOUDFLARE_IMAGE_MODEL", keyframes.DEFAULT_MODEL, required=False), params=params, seed=1, latency_s=latency, output=img)
        print(f"   wrote {img.name} in {latency:.2f}s")
        t0 = time.perf_counter()
        run_ffmpeg(["-f", "lavfi", "-i", "anullsrc=d=1", str(OUT / "smoke" / "ffmpeg-check.wav")])
        print(f"   ffmpeg ok ({time.perf_counter() - t0:.2f}s)")
    except Exception as exc:
        ok = False
        print("   FAILED:", exc)

    print("\nALL OK" if ok else "\nSome checks failed: see docs/SETUP.md and note it in FAILURES.md")
