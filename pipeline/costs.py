"""Summarise runs.jsonl per stage and model: calls, errors, total and mean latency. Feeds COSTS.md."""

from __future__ import annotations

import json
from collections import defaultdict

from pipeline.common import RUNS


def run() -> None:
    if not RUNS.exists():
        print("no runs.jsonl yet")
        return
    agg: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"calls": 0, "errors": 0, "latency": 0.0, "cost": 0.0})
    for line in RUNS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        a = agg[(row["stage"], row["model"])]
        a["calls"] += 1
        a["errors"] += 0 if row["status"] == "ok" else 1
        a["latency"] += row["latency_s"]
        a["cost"] += row.get("cost_usd") or 0
    print("| stage | model | calls | errors | total s | mean s | cost USD |")
    print("|---|---|---|---|---|---|---|")
    for (stage, model), a in sorted(agg.items()):
        ok = a["calls"] - a["errors"]
        mean = a["latency"] / ok if ok else 0
        print(f"| {stage} | {model} | {a['calls']:.0f} | {a['errors']:.0f} | {a['latency']:.1f} | {mean:.2f} | {a['cost']:.2f} |")
