# Experiments

Each entry: what I believed, what I changed, what happened (numbers from `runs.jsonl`), what I decided.

## E1: Let Gemini draft the storyboard, then edit by hand
- **Hypothesis:** a draft from my notes (`story.md`) + the schema saves time, and the schema stops bad structure.
- **Change:** `python -m pipeline draft` with gemini-2.5-flash in JSON mode.
- **Result:** 9 shots, 0 schema errors on the first try. But: it skipped the opening ("born in Riyadh, 2001"), used the
  wrong word for shiro ("الشيرا") and a stiff phrase for opening songs ("أغاني البداية" instead of "الشارات"), and
  replaced my ending with a generic one.
- **Decision:** keep the draft as a scaffold only. I rewrote it to 10 shots with my real details (running in from school,
  Dad's key in the door) and my own last line. The schema checks structure; only I can check whether it is true.

## E2: Which image model? FLUX-1 schnell vs FLUX-2 klein 4B (same prompts, shots s01 and s04)
- **Hypothesis:** schnell is faster; klein follows the "gouache storybook" style better and accepts a seed.
- **Result:**

  | | schnell | klein-4b |
  |---|---|---|
  | latency s01 / s04 | 3.4 s / 5.8 s | 12.4 s / 7.5 s |
  | seed (reproducible) | no (F5) | yes |
  | style | clean digital cartoon, not gouache | real gouache/storybook texture |
  | prompt following | TV on a rooftop (odd), planes | painted fake Arabic letters on the sky, extra people |
  | boy (s04) | clearly Ethiopian, abstract TV light | lighter skin, generic cartoon kids on the TV |

- **Decision:** klein-4b, because it looks like a painted memory and is reproducible (seed). Its problems are fixed in
  the prompts: FLUX has no negative prompt, so "no writing, no letters, no signs" went *into* the style block, the skin tone
  is described explicitly ("Ethiopian Habesha, deep dark brown skin"), and the TV "shows only soft abstract swirls of light".
- **Result after the fix (all 10 shots):** same boy in every shot, right skin tone, no fake letters, no copyrighted
  characters on the TV. Two shots needed another pass (E4).

## E3: Gemini TTS model for Arabic narration
- **Context:** forced by F4 (daily quota). Lines s01–s08 exist from gemini-2.5-flash-preview-tts and all ten from
  gemini-3.8-flash-tts, same voice (Charon) and style prompt, so the same line can be compared.
- **Result:** gemini-3.8-flash-tts read every line faithfully (radio cut 78.7 s). gemini-3.1-flash-tts-preview added
  invented sentences (F6). 3.8-flash-tts is the primary model; the others are fallbacks behind the length check.

## E4: Fixing two keyframes by changing only their prompts (cache in action)
- **s03:** the room had two TVs. Adding "a single television, only one television in the room" fixed it in one try.
- **s07:** "two Saudi boys in white thobes" came out as East Asian-looking boys, twice (once as three boys). Describing
  skin tone alone didn't help. Describing **dress** (red-and-white shemagh) plus a new seed (207) made them read as Saudi.
  Faces are still somewhat generic: an honest limit of the model's bias, noted in ETHICS.md.
- **Cache check:** after the s07 change, `film` re-rendered **only s07** (8.9 s); every other stage was a cache hit.

## E5: Rewriting the narration with a stronger writer (Claude Fable)
- **Hypothesis:** the v1 lines state facts; lines that name what is on screen and call back at the end will land harder.
- **Change:** asked Claude Fable for a rewrite under strict rules (true facts only, 4–14 words a line, full diacritics,
  keep the slogan, no cartoon names). Key ideas: the TV glow on the boy's face returns on the man's face at 25; the
  "new planet" returns as the last words ("my own planet"); the ending speaks to the viewer ("this cartoon you're
  watching? I made it myself, with AI").
- **Result:** a better script (`docs/narration-v2.md`), but recording it hit F6 and the daily quotas. Not in the film yet.

## E6: Choosing the score by measuring, not only by ear
- **Setup:** ACE-Step 1.5 turbo, one caption, 3 fixed seeds (11, 22, 33), 85 s each, A minor, 80 bpm, instrumental.
- **Hypothesis:** a score under narration should (a) leave the speech band (300–3400 Hz) as free as possible,
  (b) be steady (no swells fighting the voice), (c) last the whole film.
- **Measured** (ffmpeg `ebur128`, band-pass energy, `silencedetect`):

  | seed | LUFS | loudness range | energy in speech band | music until |
  |---|---|---|---|---|
  | 11 | −15.7 | **5.1 LU** | 25% | **80.0 s** |
  | 22 | −15.2 | 6.6 LU | 27% | 76.6 s |
  | 33 | −14.9 | 10.3 LU | **19%** | 77.9 s |

- **Decision:** seed 11. Steadiest by far and the only one that covers the full 78.7 s film (22 and 33 go silent during
  the end card). Seed 33 leaves the most room for the voice, but it swells twice as much, and the ducking would have
  to work harder. _Listening check with the narration on top: pending (me)._
- **Learned:** all three fade out at 77–80 s even when asked for 85 s, so ask for ~10 s more than needed.
