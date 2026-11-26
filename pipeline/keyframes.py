"""Stage: keyframes. One still per shot from FLUX on Cloudflare Workers AI.

The prompt is always: shot text + the fixed character descriptions + the style block (see common.image_prompt),
so characters and look stay consistent. A reference sheet is generated first (`refsheet`) to pick the look.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

import requests

from pipeline.common import Retryable, cached, check_http, env, image_prompt, key, load_storyboard, log_call, out_path, with_retries

DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"  # chosen over flux-1-schnell, see EXPERIMENTS.md E2


def _generate(prompt: str, seed: int | None, steps: int) -> tuple[bytes, float, dict[str, Any]]:
    model = env("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL, required=False)
    url = f"https://api.cloudflare.com/client/v4/accounts/{env('CLOUDFLARE_ACCOUNT_ID')}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {env('CLOUDFLARE_API_TOKEN')}"}
    params: dict[str, Any] = {"prompt": prompt[:2048], "steps": steps}
    # flux-1-schnell on Workers AI rejects a seed ("Additional properties '/seed' not allowed", see FAILURES.md),
    # so its images are not reproducible; models that accept one get it.
    if seed is not None and "flux-1-schnell" not in model:
        params["seed"] = seed

    def call() -> tuple[bytes, float, dict[str, Any]]:
        t0 = time.perf_counter()
        try:
            if "flux-2" in model:  # FLUX.2 models on Workers AI take multipart form data
                form = {k: (None, str(v)) for k, v in {**params, "width": 1024, "height": 1024}.items()}
                resp = requests.post(url, headers=headers, files=form, timeout=180)
            else:
                resp = requests.post(url, headers=headers, json=params, timeout=180)
        except requests.RequestException as exc:
            raise Retryable(str(exc)) from exc
        check_http(resp)
        body = resp.json()
        image_b64 = (body.get("result") or {}).get("image")
        if not image_b64:
            raise RuntimeError(f"no image in response: {str(body)[:300]}")
        return base64.b64decode(image_b64), time.perf_counter() - t0, params

    return with_retries(call, label=model)


def path_for(board: dict[str, Any], shot: dict[str, Any], steps: int = 4) -> Path:
    model = env("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL, required=False)
    return out_path("keyframes", shot["id"], key("keyframe-v1", model, image_prompt(board, shot), shot.get("seed"), steps), "jpg")


def run(only: set[str] | None = None, steps: int = 4) -> dict[str, Path]:
    board = load_storyboard()
    model = env("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL, required=False)
    made: dict[str, Path] = {}
    for shot in board["shots"]:
        if only and shot["id"] not in only:
            continue
        prompt = image_prompt(board, shot)
        path = path_for(board, shot, steps)
        made[shot["id"]] = path
        if cached(path, f"keyframe {shot['id']}"):
            continue
        print(f"  generate   keyframe {shot['id']}")
        try:
            data, latency, params = _generate(prompt, shot.get("seed"), steps)
        except Exception as exc:
            log_call("keyframes", model, shot=shot["id"], params={"prompt": prompt}, seed=shot.get("seed"), latency_s=0, status=f"error: {exc}"[:300])
            raise
        path.write_bytes(data)
        log_call("keyframes", model, shot=shot["id"], params=params, seed=shot.get("seed"), latency_s=latency, output=path)
    return made


def refsheet(n: int = 4, steps: int = 4) -> list[Path]:
    """Generate n candidate looks for each character (seeds 1..n) to pick a golden reference from."""
    board = load_storyboard()
    model = env("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL, required=False)
    made = []
    for char in board["characters"]:
        for seed in range(1, n + 1):
            prompt = f"Character reference sheet, full body front view and face close-up, neutral background. {char['description']}. {board['style']['block']}"
            path = out_path("refsheet", f"{char['id']}-seed{seed}", key("ref-v1", model, prompt, seed, steps), "jpg")
            made.append(path)
            if cached(path, f"ref {char['id']} seed {seed}"):
                continue
            data, latency, params = _generate(prompt, seed, steps)
            path.write_bytes(data)
            log_call("refsheet", model, shot=char["id"], params=params, seed=seed, latency_s=latency, output=path)
            print(f"  generate   ref {char['id']} seed {seed}")
    return made
