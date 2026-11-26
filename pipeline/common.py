"""Shared plumbing for every stage: paths, the storyboard, the run log, the cache and retries.

Design rules (see ARCHITECTURE.md):
* storyboard.json is the only contract between stages; a stage reads it and writes only its own outputs.
* Every output file is named by a hash of everything that went into it, so a re-run only regenerates
  what changed (change one shot's prompt -> only that shot's file has a new name).
* Every model call writes one line to runs.jsonl: stage, shot, model, params, seed, latency, cost, status.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
RUNS = ROOT / "runs.jsonl"
STORYBOARD = ROOT / "storyboard.json"
SCHEMA = ROOT / "schema" / "storyboard.schema.json"

load_dotenv(ROOT / ".env")

T = TypeVar("T")


def env(name: str, default: str | None = None, required: bool = True) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        sys.exit(f"Missing {name}. Copy .env.example to .env and fill it in (see docs/SETUP.md).")
    return value or ""


# --- storyboard ---------------------------------------------------------------------------


def load_storyboard(path: Path = STORYBOARD) -> dict[str, Any]:
    """Load and validate the storyboard. Every stage calls this first, so a broken contract stops the run."""
    from jsonschema import Draft202012Validator

    board = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(board), key=lambda e: list(e.path))
    if errors:
        lines = [f"  - {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors]
        sys.exit("storyboard.json does not match the schema:\n" + "\n".join(lines))
    ids = [s["id"] for s in board["shots"]]
    if len(ids) != len(set(ids)):
        sys.exit("storyboard.json: shot ids must be unique")
    known = {c["id"] for c in board["characters"]}
    for shot in board["shots"]:
        for cid in shot.get("characters", []):
            if cid not in known:
                sys.exit(f"storyboard.json: shot {shot['id']} uses unknown character '{cid}'")
    return board


def image_prompt(board: dict[str, Any], shot: dict[str, Any]) -> str:
    """The full image prompt: shot text + fixed character descriptions + the style block.
    Attaching the same character and style text every time is what keeps shots consistent."""
    chars = {c["id"]: c["description"] for c in board["characters"]}
    parts = [shot["image_prompt"]]
    parts += [chars[c] for c in shot.get("characters", [])]
    parts.append(board["style"]["block"])
    return ". ".join(p.strip().rstrip(".") for p in parts if p.strip()) + "."


# --- cache --------------------------------------------------------------------------------


def key(*parts: Any) -> str:
    """A short, stable hash of everything an output depends on."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def out_path(stage: str, name: str, digest: str, ext: str) -> Path:
    folder = OUT / stage
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{name}-{digest}.{ext}"


def cached(path: Path, label: str) -> bool:
    if path.exists() and path.stat().st_size > 0:
        print(f"  cache hit  {label}: {path.relative_to(ROOT)}")
        return True
    return False


# --- run log ------------------------------------------------------------------------------


def log_call(
    stage: str,
    model: str,
    *,
    shot: str | None = None,
    params: dict[str, Any] | None = None,
    seed: int | None = None,
    latency_s: float,
    status: str = "ok",
    cost_usd: float = 0.0,
    output: Path | None = None,
    note: str | None = None,
) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": stage,
        "shot": shot,
        "model": model,
        "params": params or {},
        "seed": seed,
        "latency_s": round(latency_s, 3),
        "cost_usd": cost_usd,
        "status": status,
        "output": str(output.relative_to(ROOT)).replace("\\", "/") if output else None,
    }
    if note:
        row["note"] = note
    with RUNS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# --- retries ------------------------------------------------------------------------------


class Retryable(Exception):
    """Raised for failures worth retrying (rate limit, server error, timeout)."""


def with_retries(fn: Callable[[], T], *, attempts: int = 3, base_delay: float = 4.0, label: str = "") -> T:
    """Call fn, retrying Retryable errors with exponential backoff (4 s, 8 s, ...)."""
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Retryable as exc:
            if i == attempts:
                raise
            delay = base_delay * 2 ** (i - 1)
            print(f"  retry {i}/{attempts - 1} {label}: {exc} (waiting {delay:.0f}s)")
            time.sleep(delay)
    raise AssertionError("unreachable")


def check_http(resp: Any) -> None:
    """Turn an HTTP response into Retryable (429/5xx) or a hard error (other 4xx)."""
    if resp.status_code == 429 or resp.status_code >= 500:
        raise Retryable(f"HTTP {resp.status_code}: {resp.text[:200]}")
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")


# --- ffmpeg -------------------------------------------------------------------------------


def ffmpeg_bin(name: str = "ffmpeg") -> str:
    found = shutil.which(name)
    if found:
        return found
    winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    if winget.exists():
        return str(winget)
    sys.exit(f"{name} not found. Install FFmpeg (Windows: winget install Gyan.FFmpeg; macOS: brew install ffmpeg).")


def run_ffmpeg(args: list[str]) -> None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)  # cwd=ROOT: subtitle paths stay relative
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{' '.join(cmd)}\n{proc.stderr[-2000:]}")


def duration_of(path: Path) -> float:
    out = subprocess.run(
        [ffmpeg_bin("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())
