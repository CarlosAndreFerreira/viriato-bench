#!/usr/bin/env python3
"""Agrega results.csv em pass@1. Stdlib apenas.

    python3 score.py                      # tabela markdown
    python3 score.py --json dashboard/summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results.csv"))
    ap.add_argument("--json", help="escrever sumario JSON para o dashboard")
    args = ap.parse_args()

    path = Path(args.results)
    if not path.exists():
        raise SystemExit(f"{path} nao existe - corre ./bench.sh primeiro")
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        raise SystemExit("results.csv vazio")

    grouped = defaultdict(list)
    for r in rows:
        grouped[(r.get("agent", "claude-code"), r["task"], r["side"])].append(r)

    out = []
    for (agent, task, side), rs in sorted(grouped.items()):
        scored = [r for r in rs if r.get("skip", "0") != "1"]
        skips = len(rs) - len(scored)
        k = len(scored)
        passes = sum(int(r["pass"]) for r in scored)
        walls = [w for w in (num(r["wall_s"]) for r in rs) if w is not None]
        turns = [t for t in (num(r["num_turns"]) for r in rs) if t is not None]
        costs = [c for c in (num(r["cost_usd"]) for r in rs) if c is not None]
        out.append({
            "agent": agent,
            "task": task,
            "side": side,
            "k": k,
            "skips": skips,
            "passes": f"{passes}/{k}" if k else "0/0",
            "pass_at_1": round(passes / k, 3) if k else None,
            "wall_median_s": round(statistics.median(walls)) if walls else None,
            "turns_median": round(statistics.median(turns), 1) if turns else None,
            "cost_usd_total": round(sum(costs), 4) if costs else None,
        })

    cols = ["agent", "task", "side", "k", "skips", "passes", "pass_at_1",
            "wall_median_s", "turns_median", "cost_usd_total"]
    print("| " + " | ".join(cols) + " |")
    print("|" + "|".join(["---"] * len(cols)) + "|")
    for r in out:
        print("| " + " | ".join("-" if r[c] is None else str(r[c]) for c in cols) + " |")

    flaky = [r for r in out if r["pass_at_1"] not in (None, 0.0, 1.0)]
    if flaky:
        print("\n> Instaveis (as k runs discordam entre si). Cita pass@1, nunca uma run isolada:")
        for r in flaky:
            print(f">   - {r['task']} / {r['side']} / {r['agent']}: {r['passes']}")

    skipped = [r for r in out if r["skips"]]
    if skipped:
        print("\n> Com runs em SKIP (verificador indisponivel). Estas NAO contam como pass:")
        for r in skipped:
            print(f">   - {r['task']} / {r['side']}: {r['skips']} skips")

    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nsumario -> {p}")


if __name__ == "__main__":
    main()
