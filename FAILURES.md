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

## F4: Gemini TTS ran out after 10 lines, then my retry "slept" for 20 hours
- **What broke:** generating narration stopped at shot 9 with `HTTP 429`. I first assumed a per-minute limit and changed
  the retry to wait as long as the server's `retryDelay` says. The next run looked frozen.
- **Why:** the 429 body said `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue: 10`, `retryDelay: 72454s`.
  The free TTS tier is **10 requests per day per model**; the smoke test + 8 lines + one manual test used all 10, and my
  "polite" retry obeyed a 20-hour delay.
- **Fixed:** (1) retries now stop with a clear `QuotaExhausted` message if the server asks for more than 120 s;
  (2) the quota is per model, so I moved all 10 lines to `gemini-3.8-flash-tts` (one model for every line, so the voice is
  consistent). That run also hit the per-*minute* limit twice and correctly waited ~43 s each time.
- **Lesson:** read the whole error body before writing the fix. A 429 can mean "wait a minute" or "come back tomorrow".
  Narration is now the scarcest resource: only changed lines are regenerated (cache), so edits stay cheap.

## F5: FLUX-1 schnell on Workers AI rejects a seed
- **What broke:** first keyframe call returned `HTTP 400: Additional or unevaluated properties '/seed' not allowed`.
- **Fixed:** the seed is only sent to models that accept it. Consequence: schnell images can't be reproduced from a seed,
  which is one reason to compare it with `flux-2-klein-4b` (accepts a seed), see EXPERIMENTS.md E2.

## F6: The voice model invented my memories, then read my instructions aloud
- **What broke:** after swapping in a rewritten script, the film came out at **176 s** instead of ~80 s. Line s01 (10 words)
  was 31 s long. I asked Gemini to transcribe it: the first 7 s were my line, then `gemini-3.1-flash-tts-preview` kept
  talking and **invented sentences** ("I moved to my birthplace when I was young… when I turned 10…"). In a heritage film,
  a model putting false memories in my mouth is worse than a crash.
- **Tried 1:** a strict prompt ("Read the text between the markers exactly… Voice direction: …"). Worse: the transcript
  of the next take was **my English instructions read aloud**, and no Arabic at all. One take was 655 s long.
- **Tried 2 / fixed:**
  1. Back to the short form `"<one-line direction>:\n<text>"`. Anything in a TTS prompt may be spoken, so it stays tiny.
  2. **A length check in the pipeline:** a take longer than `0.9 s × words + 3 s` is renamed `*-rejected.wav`, logged
     as `rejected` in runs.jsonl, and the next model in the chain is tried. It caught 6 bad takes automatically.
  3. **A model fallback chain** (`GEMINI_TTS_MODEL` + `GEMINI_TTS_FALLBACKS`), because the free quota is per model.
- **Where it ended:** all free TTS quotas for today were used up by the retries. The film uses the **v1 lines** from
  `gemini-3.8-flash-tts` that I had already checked in the radio cut (all served from cache, no new calls).
  The better v2 script is saved in `docs/narration-v2.md` and goes in when quota allows: only the voice lines regenerate.
- **Lessons:** (1) check outputs, not just status codes: every bad take returned HTTP 200. (2) A model can fail by
  *adding* content, so a heritage pipeline needs a check that the audio matches the text. Next step: transcribe each
  take and compare it to the script automatically.
- **Open question:** Gemini said "retry in 19.5 h" for 3.1, yet a call worked four minutes later. The server's retry
  hint is not fully reliable, so the code treats it as a hint for when to give up, not as a schedule.

## F7: The end card was cut off in the vertical export
- **What broke:** the end card is drawn on the square master; the 9:16 export keeps only the middle 1080 of 1920 px, so
  the longer lines ("Images, voice and music made with AI") were cut at both edges. Spotted by me watching the film on my phone.
- **Fixed:** the card now wraps words to fit the 9:16 safe width (85% of the middle strip) and was re-rendered.
  Lesson: anything placed on the square master must be designed for the narrowest crop.

## F8: ACE-Step crashed on Kaggle before making a sound (matplotlib backend)
- **What broke:** install and model download worked on the T4, then importing ACE-Step failed:
  `ValueError: Key backend: 'module://matplotlib_inline.backend_inline' is not a valid value for backend`.
- **Why:** Kaggle sets the environment variable `MPLBACKEND` to its notebook plotting backend. Our script runs in ACE-Step's own
  uv environment, whose matplotlib doesn't have that backend, and ACE-Step imports matplotlib indirectly (training code via lightning).
- **Fixed:** run the script with `MPLBACKEND=Agg` (a plain backend that needs no display). Lesson: a separate environment still
  inherits the parent's environment variables.
- **After the fix:** 3 candidates in 10.9 + 7.7 + 7.7 s of GPU time (model load 14 s). ACE-Step detected the pre-Ampere T4 by
  itself and used float16 instead of bfloat16, so the problem I expected (no bf16 on T4) never happened.

## F9: The music was made, then lost (Kaggle draft session ended)
- **What broke:** the three tracks were generated, but by the time I went to download them the notebook said
  "Draft Session off" and `/kaggle/working` was empty.
- **Why:** files in a draft session are temporary; they are deleted when the session stops (idle timeout).
- **Fixed:** re-ran it as a committed version (**Save Version → Save & Run All**). A committed run keeps its outputs
  permanently and is a reproducible record anyone can open. Lesson: anything I need to keep comes from a committed run.

## F10: One-pass loudness normalisation missed the target
- **What broke:** first cut with the real score measured **−15.8 LUFS, true peak −0.8 dBTP** (target −14 LUFS, peak ≤ −1).
- **Why:** single-pass `loudnorm` adjusts gain on the fly from a short window, so on a short film that starts quiet it
  undershoots; then the AAC encoder adds a little to the peak.
- **Fixed:** two passes: measure the whole mix first, then apply one linear gain from the measured values, with a
  −1.5 dBTP ceiling to leave room for AAC. Result: **−14.7 LUFS, −1.1 dBTP** in both exports (the peak limit stops it
  going louder; within 1 LU of the target).
