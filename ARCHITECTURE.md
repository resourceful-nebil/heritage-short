# Architecture

## The idea
One file, `storyboard.json`, describes the whole film. Every stage reads it and writes files under `outputs/`.
No stage talks to another directly; they meet at the storyboard and at file paths. That makes each stage replaceable
(another image model, another TTS) without touching the rest.

## The contract: `storyboard.json`
Validated against `schema/storyboard.schema.json` (JSON Schema 2020-12, `additionalProperties: false` everywhere)
before anything runs. Top level: title, logline, **audience**, **intent**, languages, style block, characters, voice,
music (caption, bpm, cues), shots (6–14), end card.

Each shot: `id`, `duration`, **`reason`** (why this shot exists; required, min length), `shot_size`, `characters`,
`image_prompt`, `motion_prompt`, `kenburns` direction, `transition_in` (`cut`/`dip`), `narration` (Arabic),
`subtitle` (English), `seed`.

The schema has earned its place: it rejected my lazy test data (F3) and a new field I forgot to declare.

## Stages
| Stage | Module | Model / tool | Writes |
|---|---|---|---|
| script (draft) | `script.py` | Gemini 2.5 Flash, JSON mode, schema in the prompt | `storyboard.draft.json` (never used directly; I edit it) |
| keyframes | `keyframes.py` | FLUX.2 klein 4B on Cloudflare Workers AI | `outputs/keyframes/<shot>-<hash>.jpg` |
| shots | `shots.py` | Wan clip if one exists, else FFmpeg Ken Burns (4× upscale + `zoompan`) | `outputs/shots/` |
| narration | `narration.py` | Gemini TTS (voice Charon), model fallback chain | `outputs/narration/<shot>-<hash>.wav` |
| music | `music.py` + `kaggle/acestep_score.ipynb` | ACE-Step 1.5 turbo on a Kaggle T4 | `outputs/music/score.wav` |
| assemble | `assemble.py` | FFmpeg | `outputs/final/film_9x16.mp4`, `film_16x9.mp4`, manifest |

**Consistency of the look** comes from composition, not luck: every image prompt is
`shot text + the fixed description of each character in the shot + the style block` (`common.image_prompt`), and home
shots repeat one fixed description of the living room (added after user test 1).

## Assembly (FFmpeg)
1. **Timing:** each shot lasts `max(storyboard duration, narration length + 0.9 s)`; the voice starts 0.4 s into its shot.
2. **Picture:** shot clips in order (dip-to-black where `transition_in: "dip"`), then the AI end card, as a square
   1024 master at 24 fps.
3. **Sound:** narration lines placed with `adelay`; the score looped/trimmed, faded in/out, and **ducked under the voice**
   with `sidechaincompress`; then **two-pass `loudnorm`** to −14 LUFS, true peak ≤ −1.5 dBTP (F10).
4. **Subtitles:** SRT from the storyboard (≤ 2 lines, ~40 chars), burned in with a style per aspect ratio.
5. **Exports:** 9:16 (1080×1920) and 16:9 (1920×1080) crops of the master; the end card text is fitted to the narrow
   9:16 crop (F7). H.264 + AAC, `+faststart`.

## Caching
Every output's file name contains `sha256(stage version, model, every input that affects it)[:12]`, for example the
keyframe key is `("keyframe-v1", model, full prompt, seed, steps)`. If the file exists, the stage skips it.
- Change one shot's prompt → only that keyframe and that Ken Burns clip are rebuilt (shown live in the walkthrough).
- Change one Arabic line → only that WAV is regenerated. This matters: TTS is the scarcest resource (10/day/model).
- A stage version string (`narration-v1`, `card-v3`) is bumped when the *code* that makes an output changes.

## Logging: `runs.jsonl`
One JSON line per model call: timestamp, stage, shot, model, params, seed, latency, status, output path, note.
Errors and rejected outputs are logged too, not only successes. `python -m pipeline costs` turns it into the table in COSTS.md.

## Failure handling
| Problem | What the pipeline does |
|---|---|
| HTTP 429 / 5xx | retry with exponential backoff (4, 8, 16 s), or the server's own `retryDelay` if longer |
| Daily quota ("retry in 20 h") | **fail fast** with a clear message instead of sleeping (F4) |
| One TTS model out of quota | next model in `GEMINI_TTS_FALLBACKS` |
| TTS returns 200 but adds speech / reads the prompt aloud | **length check** rejects takes longer than `0.9 s × words + 3 s`, keeps them as `*-rejected.wav`, logs `rejected`, tries the next model (F6) |
| TTS model returns a WAV instead of raw PCM | decoder detects `RIFF` and reads only the frames; old files repaired in place (F11) |
| No video clip for a shot | Ken Burns pan/zoom on the keyframe (allowed by the brief) |
| No score yet | quiet placeholder drone, logged as `placeholder, not the score` so it is never mistaken for the real one |
| Bad storyboard | schema validation stops the run before any API call |

## Decisions I'd defend
- **REST, no SDKs:** fewer dependencies, and I can see exactly what is sent (useful when debugging F6 and F11).
- **Ken Burns instead of Wan video:** time and GPU budget went to the score and to fixing what testers saw. The
  `shots` stage already picks up `outputs/wan/<shot>-<keyframe hash>.mp4` if a clip is added later.
- **Music chosen by measurement + ear:** loudness range, energy in the speech band, and length (EXPERIMENTS E6).
