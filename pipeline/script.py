"""Stage: script. Gemini drafts storyboard.draft.json from story.md (my own notes about the story).

The draft is never used directly: I read it, edit it, and copy it to storyboard.json myself.
The schema is sent with the prompt, and the draft is validated before it is written.
"""

from __future__ import annotations

import json
import sys

from jsonschema import Draft202012Validator

from pipeline import gemini
from pipeline.common import ROOT, SCHEMA, env, log_call

PROMPT = """You are helping me storyboard a 60-90 second personal heritage short film.
Write a storyboard as JSON that matches this JSON Schema exactly (no extra keys):

{schema}

Rules:
- 8 to 12 shots, ids s01, s02, ...; total narration about 130-200 words; shots 5-9 seconds each.
- Narration in {language_name} ({language_code}); English subtitle = faithful translation of each line.
- One idea and one gentle movement per shot. Vary shot sizes (wide to establish, close for feeling).
- image_prompt describes only what is seen (no text, signs or letters in the image). motion_prompt: only motion + camera.
- Keep characters few; reuse the same character ids so they stay consistent.
- Every shot has a one-sentence reason it exists.
- Music: a quiet instrumental underscore with no strong lead melody under narration; a theme returning at the end.
- end_card lines must say the film was made with AI.

My story notes:
---
{story}
---
Return only the JSON."""


def run(language_name: str = "Arabic", language_code: str = "ar-SA") -> None:
    story_file = ROOT / "story.md"
    if not story_file.exists():
        sys.exit("write story.md first: who, where, what happens, what the audience should feel")
    model = env("GEMINI_TEXT_MODEL", "gemini-2.5-flash", required=False)
    schema = SCHEMA.read_text(encoding="utf-8")
    prompt = PROMPT.format(schema=schema, language_name=language_name, language_code=language_code, story=story_file.read_text(encoding="utf-8"))
    text, latency, usage = gemini.generate_text(prompt, model=model, json_mode=True)
    draft = json.loads(text)
    errors = list(Draft202012Validator(json.loads(schema)).iter_errors(draft))
    out = ROOT / "storyboard.draft.json"
    out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    log_call("script", model, params={"usage": usage, "schema_errors": len(errors)}, latency_s=latency, output=out)
    print(f"  wrote {out.name} ({len(draft.get('shots', []))} shots, {len(errors)} schema errors)")
    for e in errors[:10]:
        print(f"  - {'/'.join(map(str, e.path))}: {e.message}")
