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
  to work harder. Listening check with the narration on top: done by me, it sits under the voice; all 3 testers in
  test 2 said the music helps (DESIGN.md).
- **Learned:** all three fade out at 77–80 s even when asked for 85 s, so ask for ~10 s more than needed.

## E7: How much can a TTS prompt say? (three prompt shapes)
- **Hypothesis:** a more detailed voice direction gives a better read.
- **Change → result** (same line s01; checked by transcribing the audio with Gemini):

  | prompt shape | model | result |
  |---|---|---|
  | `"<one-line style>:\n<text>"` (v1) | 3.8 Flash TTS | read the line faithfully, all 10 lines (radio cut) |
  | same, long Fable style (≈40 words) | 3.1 Flash TTS | read the line, then **invented 5 sentences** (31 s for 10 words) |
  | strict block ("read exactly… stop…" + `<<< >>>` markers) | 3.8 Flash TTS | **read my English instructions aloud**, no Arabic at all |

- **Decision:** the opposite of my hypothesis. With TTS, anything in the prompt may be spoken, so the direction stays
  one short line. Detail goes into the *text* (diacritics, punctuation for pauses), not the instructions.

## E8: Is "too long for its words" a good detector of bad takes?
- **Hypothesis:** a faithful Arabic reading takes ≤ 0.9 s per word + 3 s; anything longer has extra speech.
- **Data:** the 10 accepted lines run 3.3–7.9 s for 6–11 words (0.5–0.8 s/word). The rejected takes were 23–655 s.
- **Result:** caught **all 6** bad takes in the run. One borderline rejection (3.8 Flash-Lite, s01: 12.4 s vs a 12.0 s
  limit) was probably a good take, a likely false positive.
- **Decision:** keep it as a cheap first gate (no extra API call). It can't catch a take of the *right* length with
  wrong words; the next step would be transcribing each take and comparing it to the script.

## E9: One-pass vs two-pass loudness normalisation
- **Hypothesis:** FFmpeg's single-pass `loudnorm` is good enough for a 78 s film.
- **Result (measured with `ebur128` on the 9:16 export):**

  | version | integrated | true peak |
  |---|---|---|
  | one pass, target −14 / −1 | −15.8 LUFS | −0.8 dBTP (over the ceiling) |
  | two pass, linear, ceiling −1.5 | −14.7 LUFS | −1.1 dBTP |
  | two pass, after removing the WAV buzz (F11) | **−14.1 LUFS** | **−1.2 dBTP** |

- **Learned:** the brief's tip was right (two-pass is more accurate), and the last row taught me more: the 0 dBFS buzz
  from F11 was the loudest thing in the mix, so it had been limiting how loud everything else could go.

## E10: Opening on the boy, and a dip before the jump in time (from user test 2)
- **Hypothesis:** viewers on a feed stay if the first frame has a person in it; a fade to black makes the jump from
  boy to man feel deliberate instead of abrupt.
- **Change:** s01 redrawn as the boy at the window looking over Riyadh (same narration); new storyboard field
  `transition_in: "dip"` on s09 (0.4 s fade out and in; shot lengths unchanged so the audio doesn't move).
- **Result:** builds cleanly; the first frame now shows the main character, the city and the TV in one image.
  _Not yet tested with viewers_; that would be the first question of a third test.

## E11: Does the cache really make the film reproducible? (clean clone, no keys)
- **Hypothesis:** with every generated asset committed and named by its input hash, a stranger can rebuild the film
  without API keys and without spending any quota.
- **Test:** fresh `git clone` from GitHub into an empty folder, **no `.env`**, then `uv sync` + `python -m pipeline film`.
- **Result:** the same 77.9 s film in both aspect ratios in **47 s**; `runs.jsonl` gained **11 lines, all FFmpeg**
  (10 Ken Burns renders + 1 assembly) and **zero model calls**.
- **Side finding:** after the F11 repair each voice line got 0.16 s shorter, so 4 shots' durations changed and only
  those 4 Ken Burns clips re-rendered: duration is part of the clip's cache key, as it should be.
