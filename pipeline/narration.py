"""Stage: narration. One WAV per shot from Gemini TTS, so a re-take of one line is cheap."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline import gemini
from pipeline.common import cached, env, key, load_storyboard, log_call, out_path


def path_for(board: dict[str, Any], shot: dict[str, Any]) -> Path:
    model = env("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts", required=False)
    v = board["voice"]
    digest = key("narration-v1", model, v["name"], v["style"], board["language"]["narration"], shot["narration"])
    return out_path("narration", shot["id"], digest, "wav")


def run(only: set[str] | None = None) -> dict[str, Path]:
    board = load_storyboard()
    model = env("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts", required=False)
    v = board["voice"]
    made: dict[str, Path] = {}
    for shot in board["shots"]:
        if only and shot["id"] not in only:
            continue
        if not shot["narration"].strip():
            continue
        path = path_for(board, shot)
        made[shot["id"]] = path
        if cached(path, f"narration {shot['id']}"):
            continue
        print(f"  generate   narration {shot['id']} ({len(shot['narration'])} chars)")
        try:
            latency, usage = gemini.tts(shot["narration"], model=model, voice=v["name"], style=v["style"], out=path)
        except Exception as exc:
            log_call("narration", model, shot=shot["id"], params={"voice": v["name"]}, latency_s=0, status=f"error: {exc}"[:300])
            raise
        log_call(
            "narration",
            model,
            shot=shot["id"],
            params={"voice": v["name"], "style": v["style"], "language": board["language"]["narration"], "chars": len(shot["narration"]), "usage": usage},
            latency_s=latency,
            output=path,
        )
    return made
