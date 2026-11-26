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

- **Decision:** _pending, chosen with the director (me)._ Either way the prompts need: "no writing", a stronger skin-tone
  description, and "the TV shows only abstract coloured light".

## E3: Gemini TTS model for Arabic narration
- **Context:** forced by F4 (daily quota). Lines s01–s08 exist from gemini-2.5-flash-preview-tts and all ten from
  gemini-3.8-flash-tts, same voice (Charon) and style prompt, so the same line can be compared.
- **Result:** _to fill after listening: pronunciation of الأمهرية, الإنجيرا, البربري; pace; warmth._
