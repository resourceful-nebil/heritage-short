# Costs

**Money spent: $0.** Every model ran on a free tier. The real budget was **quota and time**, so that is what is measured.
Numbers come from `runs.jsonl` (`python -m pipeline costs`), covering *all* calls while making the film, including
failures, retries and experiments, not just one clean run.

## Per stage (all calls, 26 Nov 2026)
| stage | model | calls | errors / rejected | total s | mean s |
|---|---|---|---|---|---|
| script | gemini-2.5-flash | 1 | 0 | 23.5 | 23.5 |
| keyframes | flux-1-schnell (experiment E2) | 3 | 1 | 9.2 | 4.6 |
| keyframes | flux-2-klein-4b | 23 | 0 | 233.8 | 10.2 |
| shots | ffmpeg Ken Burns | 31 | 0 | 45.9 | 1.5 |
| narration | gemini-2.5-flash-preview-tts | 12 | 3 | 217.5 | 24.2* |
| narration | gemini-3.1-flash-tts-preview | 13 | 3 | 98.6 | 9.9 |
| narration | gemini-3.8-flash-tts (used in the film) | 14 | 3 | 66.6 | 6.1 |
| narration | gemini-3.8-flash-lite-tts | 3 | 3 | 18.4 | – |
| narration | gemini-2.5-pro-preview-tts | 1 | 1 | 0 | – |
| music | ACE-Step 1.5 turbo, Kaggle T4 | 3 | 0 | 26.3 GPU s | 8.8 |
| assemble | ffmpeg (both exports) | 10 | 0 | 1072 | 107** |

\* includes waiting out rate limits. \*\* includes narration and shot rendering triggered inside `film`, and early runs
where many stages were rebuilt.

## What one finished film actually needs
| Resource | For this film | Free allowance (as observed / stated) |
|---|---|---|
| Gemini TTS requests | 10 (one per line) | **10 per day per model** (observed in the 429 body, F4) |
| Gemini text requests | 1 draft | far above what's needed |
| Cloudflare image calls | 10 keyframes (+ re-draws) | ~10,000 "neurons"/day on Workers AI free plan |
| Kaggle GPU | ~26 s generation + 14 s model load + ~10 min install | ~30 GPU hours/week |
| Laptop (FFmpeg) | ~2–3 min for a full assembly from cached assets | – |

**Waste I can see in the numbers:** 13 of 57 TTS calls failed or were rejected (quota, invented speech, read-aloud
instructions; F4, F6). That is the most expensive lesson in the project, because TTS quota is the scarcest resource.
Most of it came from changing two things at once (new script + new model); next time I would change one at a time.

## If I had to pay
At typical paid API prices, this film would cost well under a dollar (10 short TTS lines, ~25 images, one
short text call); the GPU step is under a minute of T4 time. The cost that mattered was my hours, which is why the
cache exists: re-running the film after a change costs seconds, not quota.
