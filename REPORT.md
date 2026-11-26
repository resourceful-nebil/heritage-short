# Report: Youth of the Future / شباب المستقبل

**Repo:** https://github.com/resourceful-nebil/heritage-short · **GPU notebook:** https://www.kaggle.com/code/nebilelias/heritage-short-acestep
Every claim below points to evidence in the repository.

## 1. What I set out to make, and for whom
I was born in Riyadh in 2001 to an Ethiopian family. At home we spoke Amharic; at four o'clock I ran to the salon and
turned on Spacetoon, and I learned Arabic from the opening songs of dubbed cartoons. The channel's slogan was
"the channel of the youth of the future". The film ends on the twist that makes it mine: *this cartoon you're watching,
I made it myself, with AI*.

**Audience:** the "Spacetoon generation", people who grew up in the Gulf and the Arab world in the 2000s, especially
children of migrant families who learned Arabic from TV. **Feeling at the end:** warm nostalgia, then quiet pride.
I wrote that down before generating anything (DESIGN.md, `story.md`). While I was working, friends sent me three
Spacetoon videos (a meme, a nostalgia edit, a creator saying the cartoons made his generation love Arabic), which told
me the audience is real and still feels this. I used them as evidence only, not as material (ETHICS.md).

The result: a 78-second film, Arabic narration, English subtitles, an original ACE-Step score ducked under the voice,
10 painted keyframes with Ken Burns motion, an AI end card, exported 9:16 and 16:9 at −14.1 LUFS. One command builds it,
and a clean clone with no API keys rebuilds it in 47 s with zero model calls (EXPERIMENTS E11).

## 2. What I learned from my audience
I ran two tests with the same three people (DESIGN.md has their answers word for word).

**Test 1 (first full cut).** All three could summarise the story in one sentence, so the story worked. But the
**Dad scene said the opposite of the narration**. The line was "we waited for the sound of Dad's key in the door", and
the picture showed a man with his back to us, walking out. Person 3 said it directly ("reads as leaving, or even as
loss... the one place I stopped following"). Person 1 was more telling: they wrote that they felt something "when the
father *leaves* through the door", without noticing anything was wrong. **The picture beat the words, and I would never
have seen it myself**, because I knew what the scene meant.
- Fix: Dad seen from the front, walking *in*, boy running to him. My first retry still drew his back, because the
  *character description* said "silhouette in a lit doorway". I had to change the character, not the shot.
- Also from test 1: three TV shots in a row (s05 became the boy flying among planets), and the room changing between
  shots (one fixed description of the living room is now added to every home shot).

**Test 2 (near-final cut, real score).** 3 of 3 now read the Dad scene as an arrival. 3 of 3 said the music helps.
Two new notes: Person 2 heard a "transitional noise" (it was a real bug, see §3), and the jump from the boy to the
grown man came up for the second time (Person 3 now, Person 1 in test 1). Two tests, same note, so I treated it as real:
the storyboard got a new field, `transition_in: "dip"`, a short fade through black before the adult shot. Person 2
also asked, for the second time, for a faster opening; the first frame is now the boy at the window over Riyadh
instead of an empty skyline (E10). One note from one person (pacing outdoor → home) I deliberately left alone.

## 3. The hardest problem: the voice put words in my mouth
I swapped in a better script (rewritten with Claude Fable) and, because the first TTS model's daily quota was used up,
a different TTS model, in the same run. The film came out **176 seconds long instead of 78**. Every call had returned
HTTP 200. I had Gemini transcribe line 1: the first 7 seconds were my line, then the model **kept talking and invented
my childhood**, "I moved to my birthplace when I was young... when I turned 10...". For a heritage film that is worse
than a crash.

My first fix made it worse. I wrote a strict prompt ("read exactly the text between the markers, then stop"), and the
next take was **my English instructions read aloud**, with no Arabic at all. One take was 655 seconds long.

What solved it:
1. **Back to a one-line direction** (`"<style>:\n<text>"`). With TTS, anything in the prompt may be spoken (E7).
2. **A length check inside the pipeline:** a take longer than 0.9 s per word + 3 s is renamed `*-rejected.wav`,
   logged as `rejected`, and the next model in a fallback chain is tried. It caught all 6 bad takes (E8).
3. **A fallback chain of TTS models**, because the free quota is 10 requests per model per day (F4).
4. By then every free TTS quota was spent, so the film uses the v1 lines I had already verified in the radio cut. The
   better script waits in `docs/narration-v2.md`; with the cache, swapping it in regenerates only the voice.

A second, quieter bug came out of the same model change. Testers heard a click and a buzz at every line. I measured
instead of guessing: the first and last 30 ms of every line peaked at 0 dBFS, and the bytes after my WAV header began
with `RIFF....WAVE` again. The new model returns a **complete WAV file** where the old one returned raw audio, so my
code had wrapped a WAV inside a WAV (F11). The fix detects the header and keeps only the audio frames, and it repaired
the 10 existing files without a single new API call.

**What I take from it:** check what comes back, not the status code; and change one thing at a time. I broke that
second rule (new script + new model at once), and it cost me a day's TTS quota to untangle.

## 4. Suggested practices, tested honestly
**A practice that beat my instinct: test with people early, twice.** My instinct was to keep improving prompts and
pictures myself. The tests found the most important flaw in the film (the Dad scene) and a bug I had stopped hearing
(the clicks). Evidence: DESIGN.md test 1 → storyboard change → test 2, where 3 of 3 read the scene correctly.
A smaller one: the brief says a short style instruction beats a long one for TTS. My instinct said more direction is
better; E7 shows the brief was right in the most literal way.

**A practice that didn't work as suggested: letting the agent draft `storyboard.json`.** It saved structure work and
passed the schema on the first try (E1), but it skipped the opening ("born in Riyadh, 2001"), used the wrong word for
shiro, a stiff phrase for the opening songs, and a generic ending. I rewrote it from my own memories. The schema can
check structure; only I could check whether it was true. I'd still use it, but as scaffolding, not a draft.

I also skipped one suggested practice, the **reference sheet before keyframes**. Consistency came instead from a fixed
character description and style block attached to every prompt, and later a fixed room description. The boy stayed
the same across all 10 shots, but the room drifted until test 1 pointed it out, which is exactly what a reference
image would have prevented. So I can't claim I tested it; I can say what skipping it cost.

## 5. Beyond the floor
- **Choosing music by measurement**, not just by ear: loudness range, the share of energy in the speech band
  (300–3400 Hz), and where each track goes silent. The steadiest candidate was also the only one long enough (E6).
- **A quality gate for TTS**: the length check, and a finding about four Gemini TTS models in Arabic (3.8 Flash read
  faithfully; 3.1 Flash invented sentences; Pro had no free quota; Flash-Lite borderline), all logged in `runs.jsonl`.
- **Reproducibility proven**, not claimed: a clean clone with no keys rebuilds the film with zero model calls (E11).
- **Bias noticed and documented**: FLUX drew my Saudi friends as East Asian twice and drew me lighter-skinned until
  told otherwise (E4, ETHICS.md).
- **Image model comparison**: FLUX.1 schnell vs FLUX.2 klein on the same prompts: latency, style, seed support (E2).

What I didn't do: Wan 2.2 video (time went to the score and to fixing what testers saw; the `shots` stage already picks
up a Wan clip if one exists), a frontier comparison (no access), or a second language version.

## 6. What I'd build next
1. Record narration v2 when the quota resets, and run a third test on the new opening and the dip.
2. **An Amharic version.** My mother's language is the one missing from a film about her home; Gemini TTS claims
   Amharic, and I want to measure where it fails.
3. Replace the length gate with **transcribe-and-compare**, so a take with the right length but wrong words is caught.
4. Wan 2.2 clips for the three shots that carry the feeling (the face in the TV glow, the boy flying, Dad at the door).

*I directed Claude Code as my coding agent: it wrote most of the code; the story, the choices, the tests with people
and the decisions on every failure were mine.*
