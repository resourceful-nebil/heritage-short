"""Stage: music. The score is generated with ACE-Step 1.5 on a Kaggle GPU (kaggle/acestep_score.ipynb),
which writes candidates to outputs/music/candidates/. The chosen one is copied to outputs/music/score.wav
and the choice is written down in EXPERIMENTS.md.

Until a score exists (e.g. for the radio cut), this stage makes a quiet placeholder drone with FFmpeg
and says so loudly in the log, so a placeholder is never mistaken for the real score.
"""

from __future__ import annotations

import time
from pathlib import Path

from pipeline.common import OUT, log_call, run_ffmpeg

SCORE = OUT / "music" / "score.wav"
PLACEHOLDER = OUT / "music" / "placeholder.wav"


def placeholder(seconds: float = 120.0) -> Path:
    if PLACEHOLDER.exists():
        return PLACEHOLDER
    PLACEHOLDER.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    # a soft A-minor-ish drone: three low sines, slow tremolo, gentle low-pass
    src = "+".join(f"0.18*sin(2*PI*{f}*t)" for f in (110, 164.81, 220)) + "*(0.8+0.2*sin(2*PI*0.1*t))"
    run_ffmpeg(["-f", "lavfi", "-i", f"aevalsrc='{src}':s=48000:d={seconds}", "-af", "lowpass=f=900,afade=t=in:d=3", "-ac", "2", str(PLACEHOLDER)])
    log_call("music", "ffmpeg-placeholder-drone", params={"seconds": seconds}, latency_s=time.perf_counter() - t0, output=PLACEHOLDER, note="placeholder, not the score")
    return PLACEHOLDER


def track(allow_placeholder: bool = True) -> tuple[Path, bool]:
    """The music file to use, and whether it is the real score."""
    if SCORE.exists():
        return SCORE, True
    if not allow_placeholder:
        raise SystemExit("no outputs/music/score.wav yet: run kaggle/acestep_score.ipynb and choose a candidate")
    print("  NOTE       no score yet, using placeholder drone")
    return placeholder(), False
