# Ethics

## Consent
The film is my own story. People appear only as illustrations, never as photos, likenesses or cloned voices.

| Person | How they appear | Consent |
|---|---|---|
| Me (the author) | an anonymous illustrated boy, and the same character grown up | it's me |
| My mother | hands only, making injera; no face | **verbal consent on a phone call, 26 Nov 2026**, before the film was published. I explained what the film is, that she appears as illustrated hands, and that it will be posted publicly with an AI label. She agreed. |
| My father | an illustrated man coming home; generic face, not his likeness | **verbal consent on the same call, 26 Nov 2026**, same explanation. He agreed. |
| My Saudi friends | two illustrated boys; generic | not real individuals |

The consent was given by voice, so this table is my written record of it. I have also asked both parents to send a
one-line text confirming it, so there is a record in their own words.

**No voice cloning.** The narrator is a stock Gemini TTS voice ("Charon"), not my voice or anyone else's. Nobody's
words were put in their mouth: the only speaker is the narrator, telling my story.

## What I chose not to use
- **No Spacetoon footage, logos, characters or theme songs.** The TV in the film shows only abstract coloured light, and
  the "planets" are invented. The channel's name and slogan ("سبيستون، قناة شباب المستقبل") are quoted in the narration
  as part of a true memory, not used as branding.
- **No clips or audio from the reference videos** I was sent (a Spacetoon meme, a nostalgia edit, a creator talking
  about learning Arabic from cartoons). I used them only as evidence that the audience exists (DESIGN.md). One shows a
  real person's face, and the cartoons and their music belong to their owners. I wanted the background sound of one of
  them and decided against it; the score is generated.
- No named cartoon in the script, even though Dragon Ball and Detective Conan are the ones I watched.
- No private family details beyond what is in the film were sent to the free APIs.

## Truthfulness
- Everything in the narration is true (`story.md`, DESIGN.md).
- When a TTS model **invented sentences** about my childhood (FAILURES.md F6), I treated it as an ethical failure, not
  just a bug: a heritage film can't put false memories in my mouth. The pipeline now rejects takes whose length doesn't
  fit the script, and keeps every rejected take logged.

## Models and licences (as stated by each provider at the time of use)
| Use | Model | Access | Licence / terms |
|---|---|---|---|
| Images | FLUX.2 [klein] 4B (Black Forest Labs) | Cloudflare Workers AI | Apache 2.0 (the 9B klein is non-commercial; I used 4B) |
| Image test only | FLUX.1 [schnell] | Cloudflare Workers AI | Apache 2.0 |
| Voice | Gemini 3.8 Flash TTS | Gemini API free tier | Gemini API terms; free-tier inputs may be used by Google to improve models, so only the script was sent |
| Storyboard draft | Gemini 2.5 Flash | Gemini API free tier | same |
| Music | ACE-Step 1.5 turbo | my own run on a Kaggle T4 | MIT; outputs usable commercially; trained on licensed, royalty-free and synthetic data |
| Assembly | FFmpeg | my laptop | LGPL/GPL tool; not AI |
| Narration rewrite v2 (not recorded yet) | Claude Fable | via my coding agent | Anthropic terms |
| Coding agent | Claude Code | — | I directed it; story, choices and testing are mine |

## Bias I noticed
FLUX drew my Saudi friends as East Asian-looking boys twice, even when asked for Saudi boys; only describing their dress
(thobe and shemagh) fixed it, and their faces are still generic (EXPERIMENTS E4). It also first drew me lighter-skinned
until the description said "deep dark brown skin". The default "boy" in these models is not a boy who looks like me,
so I had to say so in every prompt.

## Labelling
- The film ends on a card: **"Images, voice and music made with AI"** (fitted to the 9:16 safe area, F7).
- The public post has the platform's **AI-generated label switched on**, and the caption says it was made with AI.
- Files are exported as generated; I did not strip any provenance metadata.
- The README names every model used.
