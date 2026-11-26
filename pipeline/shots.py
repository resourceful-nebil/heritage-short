"""Stage: moving shots. Uses a Wan 2.2 image-to-video clip when one exists for the current keyframe,
otherwise falls back to a slow Ken Burns pan/zoom over the keyframe (made locally with FFmpeg, no GPU).

Wan clips are made on Kaggle (kaggle/wan_i2v.ipynb) and dropped in outputs/wan/ named <shot>-<keyframe hash>.mp4,
so a clip is only used while its keyframe is unchanged: change the keyframe and the stale clip is ignored.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from pipeline import keyframes
from pipeline.common import OUT, cached, key, load_storyboard, log_call, out_path, run_ffmpeg

FPS = 24
SIZE = 1024

MOVES = {  # zoompan expressions: zoom, x, y
    "in": ("min(zoom+0.0009,1.18)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "out": ("if(eq(on,0),1.18,max(zoom-0.0009,1.0))", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "left": ("1.15", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
    "right": ("1.15", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    "up": ("1.15", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/{n})"),
    "down": ("1.15", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*on/{n}"),
}


def wan_clip(keyframe: Path, shot_id: str) -> Path | None:
    digest = keyframe.stem.split("-")[-1]
    clip = OUT / "wan" / f"{shot_id}-{digest}.mp4"
    return clip if clip.exists() else None


def kenburns(image: Path, out: Path, seconds: float, move: str) -> None:
    n = max(1, round(seconds * FPS))
    z, x, y = (expr.replace("{n}", str(n)) for expr in MOVES[move])
    vf = (
        f"scale={SIZE * 4}:-1,"  # upscale first: zoompan on a small image jitters
        f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={SIZE}x{SIZE}:fps={FPS},"
        "format=yuv420p"
    )
    run_ffmpeg(["-loop", "1", "-i", str(image), "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])


def fit_clip(clip: Path, out: Path, seconds: float) -> None:
    """Scale/crop a Wan clip to the square master, trim its weak first 0.3 s, hold the last frame if short."""
    vf = (
        f"trim=start=0.3,setpts=PTS-STARTPTS,fps={FPS},"
        f"scale={SIZE}:{SIZE}:force_original_aspect_ratio=increase,crop={SIZE}:{SIZE},"
        f"tpad=stop_mode=clone:stop_duration={seconds},format=yuv420p"
    )
    run_ffmpeg(["-i", str(clip), "-vf", vf, "-t", f"{seconds:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])


def run(durations: dict[str, float], only: set[str] | None = None) -> dict[str, Path]:
    """Render every shot at its final duration (assembly decides durations from narration length)."""
    board = load_storyboard()
    made: dict[str, Path] = {}
    for shot in board["shots"]:
        if only and shot["id"] not in only:
            continue
        kf = keyframes.path_for(board, shot)
        if not kf.exists():
            raise SystemExit(f"missing keyframe for {shot['id']}: run `python -m pipeline keyframes` first")
        seconds = durations[shot["id"]]
        clip = wan_clip(kf, shot["id"])
        source = "wan" if clip else "kenburns"
        move = shot.get("kenburns", "in")
        path = out_path("shots", shot["id"], key("shot-v1", source, kf.name, clip.name if clip else move, round(seconds, 2)), "mp4")
        made[shot["id"]] = path
        if cached(path, f"shot {shot['id']} ({source})"):
            continue
        print(f"  render     shot {shot['id']} via {source} ({seconds:.1f}s)")
        t0 = time.perf_counter()
        if clip:
            fit_clip(clip, path, seconds)
        else:
            kenburns(kf, path, seconds, move)
        # not a model call (local FFmpeg), but logged so COSTS.md can show where the time goes
        log_call("shots", f"ffmpeg-{source}", shot=shot["id"], params={"seconds": round(seconds, 2), "move": move}, latency_s=time.perf_counter() - t0, output=path)
    return made


def placeholder_keyframe(text: str, path: Path) -> None:
    """Used only by the radio cut / tests when no keyframes exist yet."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (SIZE, SIZE), (10, 10, 10))
    ImageDraw.Draw(img).text((40, SIZE // 2), text, fill=(200, 200, 200))
    img.save(path)


def describe(board: dict[str, Any]) -> list[str]:
    return [f"{s['id']}: {'wan' if wan_clip(keyframes.path_for(board, s), s['id']) else 'kenburns'}" for s in board["shots"]]
