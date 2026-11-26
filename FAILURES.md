# Failures

What broke, what I tried, what fixed it. Newest at the bottom.

## F1: Default Python was a 3.15 alpha
- **What broke:** the machine's default `python` is 3.15.0a7 (a pre-release); many packages don't publish wheels for it yet.
- **Tried / fixed:** pinned the project to Python 3.12 with `uv python pin 3.12`, so `uv sync` builds a known-good environment.
  A stranger cloning the repo gets the same version from `.python-version`.

## F2: Vertical subtitles wrapped to four lines
- **What broke:** in the first offline test render, a 70-character subtitle filled four lines in the 9:16 export
  (libass re-wraps text when the font is wide relative to the 1080 px frame), covering the middle of the picture.
- **Tried / fixed:** kept my own wrap (≤ 2 lines, ~40 chars) and lowered the 9:16 font size from 13 to 9 (libass units),
  margin 60 so it sits above the platform buttons. Re-rendered: two lines, inside the safe area.

## F3: Schema rejected my own test storyboard
- **What broke:** `validate` refused a quick test board ("reason: 'r' is too short", prompts too short).
- **Result:** not a bug, the contract doing its job. Kept the minimum lengths, because a shot without a stated reason is
  exactly what the design brief warns against.
