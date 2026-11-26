# Design

## Who it is for
The **Spacetoon generation**: people who grew up in the Gulf and the Arab world in the 2000s, especially children of
migrant families who learned Arabic from dubbed cartoons. I am one of them: born in Riyadh in 2001 to an Ethiopian
family, Amharic at home, Arabic from the TV.

**Evidence this audience exists and still feels it:** short videos shared with me on Telegram while I was making this:
a "POV: Spacetoon's message" meme, a nostalgic edit of the old cartoons ("peace be upon the days when nothing bothered
us but…"), and a creator explaining that the dubbed cartoons are what made his generation love Arabic. That last one is
exactly my story. I did not use any of their footage (the cartoons belong to others, and one shows a real person's face).

## The feeling at the end
Warm nostalgia, then quiet pride: *two homes, one childhood*, and the promise of "the youth of the future" coming true.
The film itself is the proof: the boy who watched cartoons made this one.

## Choices that follow from the audience
- **Arabic narration, English subtitles:** Arabic is the language I learned from the TV, so the story is told in it.
  Subtitles carry it to everyone else, including my own Amharic-speaking family.
- **No real cartoon on screen:** the TV shows only abstract coloured light, and the "planets" are invented. My audience
  fills in their own favourite show, which works better than any clip, and it keeps the film legally clean.
- **Vertical first (9:16):** this audience meets these memories on phones, in feeds (like the videos above).

---

## User test 1: first full cut (pictures + narration, placeholder music), 26 Nov 2026
Sent `film_9x16.mp4` to 3 people. Same three questions. Answers are copied word for word.

### Person 1
1. **What was it about?** "It was about growing up in Riyadh, discovering the world through cartoons, and how those
   childhood experiences shaped who I am today."
2. **Where did you feel something?** "When the father leaves through the door and the child waits for him to return.
   It brought a sense of childhood nostalgia and family memories."
3. **Bored or confused?** "I didn't find any particular part boring or confusing, but the transition from childhood
   memories to the present-day version of the narrator could have been a little smoother."

### Person 2
1. **What was it about?** "It is a personal reflection of a person born in Riyadh to Ethiopian parents who learned Arabic
   through Spacetoon cartoons, which ultimately inspired them to become an animator today."
2. **Where did you feel something?** "The transition when the narrator describes running home from school to watch
   Spacetoon ('شباب المستقبل') and traveling alone to those glowing animated worlds, showing how art and media can deeply
   connect someone to a new language and culture across borders."
3. **Bored or confused?** "The narrative flows smoothly and is cohesive throughout its short runtime, so there are no
   confusing or dragging moments."

### Person 3
1. **What was it about?** "A boy born in Riyadh to an Amharic-speaking family learns Arabic and finds belonging through
   Spacetoon cartoons, and grows up to make cartoons himself."
2. **Where did you feel something?** "The ending (~1:06–1:12), the grown man at his laptop with his younger self on the
   screen [...] It turns Spacetoon's slogan 'youth of the future' from a childhood memory into a promise fulfilled. It
   works because you set up the phrase at 0:24 and paid it off at the end." Also 0:38–0:43, "I learned Arabic from the
   opening songs", boy with arms flung wide.
3. **Bored or confused?**
   - "The dad scene (0:53–0:59) confused me. [...] The image shows a man with his back to us, walking *out* through a
     bright doorway, which reads as leaving, or even as loss. [...] it's the one place I stopped following the story."
   - "The opening is slow for a vertical short. The skyline holds for about 7 seconds and the injera shot for about 8."
   - "The middle sags a little (0:24–0:43): three shots in a row of the boy in front of the TV."
   - "The room and the boy change between shots. The rug, the walls (planet wallpaper appears at 0:30)..."

### What I learned
- **The story lands.** All three summed it up correctly in one sentence, without help. The setup and payoff of
  "youth of the future" works (Person 3 named the exact timestamps).
- **The dad shot said the opposite of the narration.** Person 3 said so directly. Person 1 *felt* it but read it the
  wrong way ("when the father leaves through the door"). So 2 of 3 saw a father leaving where I meant one arriving.
  The picture beat the words. This is the most important fix.
- Pictures drift: the room changed from shot to shot because each prompt described it differently.

### What I changed (and what I didn't)
| Feedback | Change | Result |
|---|---|---|
| Dad reads as leaving (P1, P3) | s08: father seen **from the front, walking in**, door open behind him, boy running to him. The first retry still drew his back: the character description itself said "silhouette in a lit doorway", so I rewrote the character, not just the shot | He now clearly arrives |
| Three TV shots in a row (P3) | s05 now shows the boy **flying among invented planets**, inside his imagination, instead of a fourth TV shot | Variety in the middle; same narration |
| Room changes between shots (P3) | One fixed description of the living room (beige walls, blue/red carpet, cushions, one CRT TV, white curtains) added to every home shot; s04 re-seeded to keep the striped shirt | Same room in s03–s06, s08 |
| Slow opening (P3) | **Not changed yet.** Each shot is as long as its narration line, and today's free TTS quota is used up (FAILURES.md F4, F6). The shorter, sharper v2 lines in `docs/narration-v2.md` fix this when quota returns | Logged |
| Child-to-adult jump (P1) | Not changed yet; candidate: a short dissolve between s08 and s09 | For test 2 |

Only the five changed shots were re-rendered (cache); everything else, including all narration, was reused.

## User test 2: near-final cut (real score, test-1 fixes), 26 Nov 2026
Same 3 people, new questions aimed at what I changed. Answers copied word for word (lightly trimmed where marked).

### Person 1
1. **Did the Dad scene make sense this time?** "Yes, it fits naturally now. The mention of waiting for the father's key at
   the door ('صوت مفتاح أبي في الباب') grounds the nostalgic childhood memories of cartoons and food in the warmth of a
   real family home environment."
2. **Does the music help or distract?** "It definitely helps. The gentle, nostalgic background score enhances the
   emotional weight of growing up between two cultures [...]"
3. **One thing you'd still change?** "The pacing could be slightly smoothed out right around the transition from the
   outdoor neighborhood scenes back to the home evening routine, giving the visual rhythm a bit more breathing room."

### Person 2
1. "Yes, the Dad scene works now. He's walking *in* through the open door with his briefcase, facing us, and the boy is
   running up to grab his hand. The picture and the line [...] finally say the same thing. [...] It also gives the film
   an emotional beat right before the jump to adulthood, so the ending lands harder than before." Also noticed the
   planets shot breaks up the TV shots and "the living room (the blue rug, the lamp, the TV) stays consistent".
2. "Remove the transitional noise."
3. "The one thing I'd still change is the opening. The first 16 seconds are still two nearly still images [...] on a
   vertical feed a lot of viewers decide in the first 2–3 seconds. I'd cut the skyline to about 3 seconds, or open on
   the boy and let 'I was born in Riyadh in 2001' play over him."

### Person 3
1. "Yes, it makes more sense now. The father returning and holding the child's hand connects better with the childhood
   memories and the emotional message."
2. "The music helps. It adds to the nostalgic atmosphere and makes the childhood memories feel more emotional without
   taking away from the story."
3. "I'd make the transition between the childhood memories and the present-day version of the narrator a little smoother.
   That would make the ending more impactful."

### What I learned
- **The test-1 fix worked:** 3 of 3 now read the Dad scene as an arrival. The picture and the words agree.
- **The music works** (3 of 3), but there was a **noise at the transitions** (Person 2, and me). It turned out to be a
  decoding bug, not the music (FAILURES.md F11).
- **The child-to-adult jump** came up again (Person 3, and Person 1 in test 1): two tests, same note, so it is real.
- **The opening** came up again (Person 2, both tests).

### What I changed
| Feedback | Change |
|---|---|
| Transition noise (P2) | Found and fixed a WAV-inside-a-WAV bug: click + 0.16 s buzz at every line (F11) |
| Slow opening (P2, twice) | s01 now **opens on the boy** at the window, looking out over Riyadh's satellite dishes and a minaret, with the TV already in the room. The tester's own suggestion. |
| Child-to-adult jump (P3; P1 in test 1) | New storyboard field `transition_in: "dip"`: a 0.4 s fade to black and back before s09, so the jump in time reads as deliberate |
| Pacing outdoor → home (P1) | Not changed: one note from one person; the dip now marks the bigger jump |

I also wanted to use the background sound from one of the Spacetoon videos I was sent. I didn't: it belongs to
someone else, and the brief asks for original music. The score is my own ACE-Step track (EXPERIMENTS.md E6).
