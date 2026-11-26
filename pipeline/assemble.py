"""Stage: assembly (FFmpeg only, deterministic). Builds the film from the storyboard and the other stages' outputs:

  timings   each shot lasts max(storyboard duration, its narration + 0.9 s)
  picture   shots in order + the AI end card                      -> square master (1024x1024, 24 fps)
  voice     each narration line placed 0.4 s into its shot
  music     score looped/trimmed to length, faded, ducked under the voice (sidechaincompress)
  loudness  final mix normalised to -14 LUFS, true peak -1 dB (loudnorm)
  subtitles English, burned in, inside the safe area of each aspect ratio
  exports   9:16 (1080x1920) and 16:9 (1920x1080), H.264 + AAC

`radio` mode is the cheap prototype: narration + music over a black screen, no pictures needed.
"""

from __future__ import annotations

import json
import textwrap
import time
from pathlib import Path
from typing import Any

from pipeline import music, narration, shots
from pipeline.common import OUT, ROOT, duration_of, key, load_storyboard, log_call, run_ffmpeg

LEAD_IN = 0.4
TAIL = 0.5
FINAL = OUT / "final"
WORK = OUT / "assembly"
EXPORTS = {
    "9x16": {"vf": "scale=1920:1920,crop=1080:1920", "style": "FontName=Arial,FontSize=9,Outline=1,Shadow=0,MarginV=60,Alignment=2"},
    "16x9": {"vf": "scale=1920:1920,crop=1920:1080", "style": "FontName=Arial,FontSize=18,Outline=1.2,Shadow=0,MarginV=28,Alignment=2"},
}


def timings(board: dict[str, Any]) -> tuple[dict[str, float], dict[str, Path]]:
    voice = narration.run()  # cached: only missing lines are generated
    durs = {}
    for shot in board["shots"]:
        d = float(shot["duration"])
        if shot["id"] in voice:
            d = max(d, duration_of(voice[shot["id"]]) + LEAD_IN + TAIL)
        durs[shot["id"]] = round(d, 2)
    return durs, voice


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def write_srt(board: dict[str, Any], durs: dict[str, float], voice: dict[str, Path], path: Path) -> None:
    rows, start, n = [], 0.0, 1
    for shot in board["shots"]:
        if shot["subtitle"].strip() and shot["id"] in voice:
            a = start + LEAD_IN
            b = min(start + durs[shot["id"]], a + duration_of(voice[shot["id"]]) + 0.2)
            text = "\n".join(textwrap.wrap(shot["subtitle"], 40)[:2])  # max 2 lines, ~40 chars
            rows.append(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n")
            n += 1
        start += durs[shot["id"]]
    path.write_text("\n".join(rows), encoding="utf-8")


def end_card(board: dict[str, Any], path: Path, seconds: float) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (shots.SIZE, shots.SIZE), (8, 8, 8))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default(size=40)
    lines = board["end_card"]["lines"]
    y = shots.SIZE // 2 - len(lines) * 30
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((shots.SIZE - w) / 2, y), line, fill=(235, 235, 235), font=font)
        y += 60
    still = path.with_suffix(".png")
    img.save(still)
    n = round(seconds * shots.FPS)
    run_ffmpeg(["-loop", "1", "-i", str(still), "-vf", f"fps={shots.FPS},fade=t=in:d=0.6,format=yuv420p", "-frames:v", str(n), "-c:v", "libx264", "-crf", "18", str(path)])


def mix_audio(board: dict[str, Any], durs: dict[str, float], voice: dict[str, Path], total: float, out: Path, music_file: Path) -> None:
    inputs, delays, start = [], [], 0.0
    for shot in board["shots"]:
        if shot["id"] in voice:
            inputs.append(voice[shot["id"]])
            delays.append(round((start + LEAD_IN) * 1000))
        start += durs[shot["id"]]
    args: list[str] = []
    for p in inputs:
        args += ["-i", str(p)]
    args += ["-stream_loop", "-1", "-i", str(music_file)]
    m = len(inputs)
    parts = [f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={d}|{d}[v{i}]" for i, d in enumerate(delays)]
    parts.append("".join(f"[v{i}]" for i in range(m)) + f"amix=inputs={m}:normalize=0,apad,atrim=0:{total:.3f},asplit=2[voice][sc]")
    parts.append(f"[{m}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},afade=t=in:d=2,afade=t=out:st={total - 3:.3f}:d=3,volume=0.55[mus]")
    parts.append("[mus][sc]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[ducked]")
    parts.append("[voice][ducked]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=11[out]")
    run_ffmpeg([*args, "-filter_complex", ";".join(parts), "-map", "[out]", "-ar", "48000", "-t", f"{total:.3f}", str(out)])


def run(mode: str = "film") -> dict[str, Path]:
    board = load_storyboard()
    WORK.mkdir(parents=True, exist_ok=True)
    FINAL.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    durs, voice = timings(board)
    card_s = float(board["end_card"].get("duration", 3))
    total = round(sum(durs.values()) + card_s, 3)
    music_file, real_score = music.track()

    # picture
    if mode == "radio":
        master = WORK / "radio_black.mp4"
        run_ffmpeg(["-f", "lavfi", "-i", f"color=c=black:s={shots.SIZE}x{shots.SIZE}:r={shots.FPS}:d={total}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(master)])
        picture = ["radio"]
    else:
        clips = shots.run(durs)
        card = WORK / f"endcard-{key('card-v1', board['end_card'])}.mp4"
        if not card.exists():
            end_card(board, card, card_s)
        listing = WORK / "concat.txt"
        order = [clips[s["id"]] for s in board["shots"]] + [card]
        listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in order), encoding="utf-8")
        master = WORK / "master.mp4"
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(master)])
        picture = [p.name for p in order]

    # sound + subtitles
    mix = WORK / "mix.wav"
    mix_audio(board, durs, voice, total, mix, music_file)
    srt = WORK / "subs.srt"
    write_srt(board, durs, voice, srt)

    # exports
    made = {}
    for name, spec in EXPORTS.items():
        out = FINAL / f"{mode}_{name}.mp4"
        vf = f"{spec['vf']},subtitles={srt.relative_to(ROOT).as_posix()}:force_style='{spec['style']}',format=yuv420p"
        run_ffmpeg(["-i", str(master), "-i", str(mix), "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)])
        made[name] = out

    manifest = {"mode": mode, "total_s": total, "durations": durs, "real_score": real_score, "music": music_file.name, "picture": picture,
                "shot_sources": shots.describe(board) if mode != "radio" else [], "exports": {k: str(v.relative_to(ROOT)) for k, v in made.items()}}
    (FINAL / f"{mode}_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log_call("assemble", "ffmpeg", params={"mode": mode, "total_s": total, "real_score": real_score}, latency_s=time.perf_counter() - t0, output=made["9x16"])
    print(f"  done       {mode}: {total:.1f}s -> " + ", ".join(str(p.relative_to(ROOT)) for p in made.values()))
    return made
