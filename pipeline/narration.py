"""Stage: narration. One WAV per shot from Gemini TTS, so a re-take of one line is cheap.

Free-tier TTS allows ~10 requests per day *per model* (FAILURES.md F4), so models form a chain:
GEMINI_TTS_MODEL first, then GEMINI_TTS_FALLBACKS (comma-separated). For each line the cache is checked for every
model in the chain; a new line is generated with the first model whose daily quota is not used up.
Same voice name and style on every model, and runs.jsonl records which model made which line.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline import gemini
from pipeline.common import QuotaExhausted, cached, duration_of, env, key, load_storyboard, log_call, out_path

DEFAULT_MODEL = "gemini-3.8-flash-tts"
DEFAULT_FALLBACKS = "gemini-3.1-flash-tts-preview,gemini-3.8-flash-lite-tts,gemini-2.5-flash-preview-tts"


def max_seconds(text: str) -> float:
    """Upper bound for a faithful reading: slow narration is ~0.6-0.8 s per Arabic word; allow 0.9 s/word + 3 s of pauses."""
    return 0.9 * len(text.split()) + 3.0


def models() -> list[str]:
    chain = [env("GEMINI_TTS_MODEL", DEFAULT_MODEL, required=False)]
    chain += [m.strip() for m in env("GEMINI_TTS_FALLBACKS", DEFAULT_FALLBACKS, required=False).split(",") if m.strip()]
    return list(dict.fromkeys(chain))  # de-duplicate, keep order


def path_for(board: dict[str, Any], shot: dict[str, Any], model: str) -> Path:
    v = board["voice"]
    # "narration-v1" = prompt "{style}:\n{text}" (gemini.tts). Bump it whenever the prompt template changes.
    digest = key("narration-v1", model, v["name"], v["style"], board["language"]["narration"], shot["narration"])
    return out_path("narration", shot["id"], digest, "wav")


def existing(board: dict[str, Any], shot: dict[str, Any]) -> Path | None:
    """A cached take of this exact line from any model in the chain (primary model preferred)."""
    for model in models():
        path = path_for(board, shot, model)
        if path.exists():
            return path
    return None


def run(only: set[str] | None = None) -> dict[str, Path]:
    board = load_storyboard()
    v = board["voice"]
    made: dict[str, Path] = {}
    exhausted: set[str] = set()
    for shot in board["shots"]:
        if only and shot["id"] not in only:
            continue
        if not shot["narration"].strip():
            continue
        hit = existing(board, shot)
        if hit and cached(hit, f"narration {shot['id']}"):
            made[shot["id"]] = hit
            continue
        for model in models():
            if model in exhausted:
                continue
            path = path_for(board, shot, model)
            print(f"  generate   narration {shot['id']} ({len(shot['narration'])} chars) with {model}")
            try:
                latency, usage = gemini.tts(shot["narration"], model=model, voice=v["name"], style=v["style"], out=path)
            except QuotaExhausted as exc:
                log_call("narration", model, shot=shot["id"], params={"voice": v["name"]}, latency_s=0, status=f"quota: {exc}"[:300])
                print(f"  quota      {model} used up for today, trying the next model")
                exhausted.add(model)
                continue
            except Exception as exc:
                log_call("narration", model, shot=shot["id"], params={"voice": v["name"]}, latency_s=0, status=f"error: {exc}"[:300])
                raise
            seconds, limit = duration_of(path), max_seconds(shot["narration"])
            if seconds > limit:
                # far longer than the words allow: the model added speech of its own (F6). Never use it silently.
                rejected = path.with_name(path.stem + "-rejected.wav")
                path.replace(rejected)
                log_call("narration", model, shot=shot["id"], params={"seconds": round(seconds, 1), "limit": round(limit, 1)}, latency_s=latency,
                         status="rejected: too long for the text (model added words?)", output=rejected)
                print(f"  REJECTED   {shot['id']}: {seconds:.1f}s for {len(shot['narration'].split())} words (limit {limit:.1f}s), trying the next model")
                continue
            log_call(
                "narration",
                model,
                shot=shot["id"],
                params={"voice": v["name"], "style": v["style"], "language": board["language"]["narration"], "chars": len(shot["narration"]), "usage": usage},
                latency_s=latency,
                output=path,
            )
            made[shot["id"]] = path
            break
        else:
            raise QuotaExhausted(f"every TTS model in the chain is out of quota today: {models()}")
    return made
