"""One entry point for every stage.

    python -m pipeline smoke                 call each provider once (latency -> runs.jsonl)
    python -m pipeline validate              check storyboard.json against the schema
    python -m pipeline draft                 Gemini drafts storyboard.draft.json from story.md
    python -m pipeline narration [s03 ...]   Gemini TTS, one WAV per shot (cached)
    python -m pipeline refsheet              candidate character looks (seeds 1-4)
    python -m pipeline keyframes [s03 ...]   FLUX keyframes (cached)
    python -m pipeline music import <zip>    unpack + log the Kaggle ACE-Step candidates
    python -m pipeline music choose seed22   make one candidate the score
    python -m pipeline radio                narration + music over black (the cheap prototype)
    python -m pipeline film                  everything: narration, keyframes, shots, music, assembly
    python -m pipeline costs                 summarise runs.jsonl into a per-stage table

Every stage is cached by a hash of its inputs: re-running `film` after editing one shot
regenerates only that shot's files.
"""

from __future__ import annotations

import sys

from pipeline.common import load_storyboard


def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    only = set(rest) or None
    if cmd == "smoke":
        from pipeline import smoke

        smoke.run()
    elif cmd == "validate":
        board = load_storyboard()
        print(f"storyboard.json OK: {len(board['shots'])} shots, {sum(s['duration'] for s in board['shots']):.0f}s planned")
    elif cmd == "draft":
        from pipeline import script

        script.run()
    elif cmd == "narration":
        from pipeline import narration

        narration.run(only)
    elif cmd == "refsheet":
        from pipeline import keyframes

        keyframes.refsheet()
    elif cmd == "keyframes":
        from pipeline import keyframes

        keyframes.run(only)
    elif cmd in ("radio", "film"):
        from pipeline import assemble, keyframes

        print(f"== {cmd} ==")
        if cmd == "film":
            keyframes.run()
        assemble.run(cmd)
    elif cmd == "music":
        from pipeline import music

        if len(rest) == 2 and rest[0] == "import":
            music.import_candidates(rest[1])
        elif len(rest) == 2 and rest[0] == "choose":
            music.choose(rest[1])
        else:
            sys.exit("usage: python -m pipeline music import <score_candidates.zip> | music choose <seed22>")
    elif cmd == "costs":
        from pipeline import costs

        costs.run()
    else:
        sys.exit(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv[1:])
