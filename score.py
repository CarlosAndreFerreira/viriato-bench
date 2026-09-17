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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_ts(v):
    try:
        return datetime.fromisoformat(v)
    except (TypeError, ValueError):
        return datetime.min


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results.csv"))
    ap.add_argument("--json", help="escrever sumario JSON para o dashboard")
    ap.add_argument("--all-batches", action="store_true",
                     help="junta todos os batches de bench.sh no mesmo denominador "
                          "(por omissao usa-se so o batch mais recente por task/side)")
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

    # results.csv e append-only: linhas antigas (sem batch_id) contam como um
    # unico batch partilhado "" para nao rebentar, mas correr bench.sh outra
    # vez sobre um results.csv antigo vai imediatamente separa-las.
    multi_batch_groups = []
    out = []
    for (agent, task, side), rs in sorted(grouped.items()):
        batches = sorted({r.get("batch_id", "") for r in rs})
        if not args.all_batches and len(batches) > 1:
            latest_ts = {b: max(parse_ts(r["ts"]) for r in rs if r.get("batch_id", "") == b) for b in batches}
            latest_batch = max(latest_ts, key=latest_ts.get)
            dropped = len(rs) - sum(1 for r in rs if r.get("batch_id", "") == latest_batch)
            multi_batch_groups.append((agent, task, side, latest_batch, batches, dropped))
            rs = [r for r in rs if r.get("batch_id", "") == latest_batch]
        scored = [r for r in rs if r.get("skip", "0") != "1"]
        skips = len(rs) - len(scored)
        k = len(scored)
        passes = sum(int(r["pass"]) for r in scored)
        walls = [w for w in (num(r["wall_s"]) for r in rs) if w is not None]
        turns = [t for t in (num(r["num_turns"]) for r in rs) if t is not None]
        costs = [c for c in (num(r["cost_usd"]) for r in rs) if c is not None]
        # agent_exit/timeout_hit existem em runs recentes (bench.sh); results.csv
        # antigos nao tem a coluna - get() com default "0" mantem isso silencioso.
        timeouts = sum(1 for r in rs if r.get("timeout_hit", "0") == "1")
        agent_fails = sum(1 for r in rs if r.get("agent_exit", "0") not in ("0", ""))
        out.append({
            "agent": agent,
            "task": task,
            "side": side,
            "batches": sorted({r.get("batch_id", "") for r in rs}),
            "k": k,
            "skips": skips,
            "passes": f"{passes}/{k}" if k else "0/0",
            "pass_at_1": round(passes / k, 3) if k else None,
            "wall_median_s": round(statistics.median(walls)) if walls else None,
            "turns_median": round(statistics.median(turns), 1) if turns else None,
            "cost_usd_total": round(sum(costs), 4) if costs else None,
            "timeouts": timeouts,
            "agent_fails": agent_fails,
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

    if multi_batch_groups:
        print("\n> Mais do que um batch de bench.sh encontrado para o mesmo task/side."
              " A usar so o mais recente (--all-batches para juntar tudo):")
        for agent, task, side, latest_batch, batches, dropped in multi_batch_groups:
            print(f">   - {task} / {side} / {agent}: batch ativo {latest_batch!r}"
                  f" ({len(batches)} batches no total, {dropped} runs mais antigas ignoradas)")

    harness_fails = [r for r in out if r["agent_fails"]]
    if harness_fails:
        print("\n> Com falhas do agente antes do verificador correr (timeout, crash, auth, quota)."
              " Contam para pass@1 como fail, mas NAO sao 'o modelo respondeu errado':")
        for r in harness_fails:
            bits = [f"{r['timeouts']} timeout" if r["timeouts"] else None,
                    f"{r['agent_fails'] - r['timeouts']} outro exit!=0" if r["agent_fails"] > r["timeouts"] else None]
            print(f">   - {r['task']} / {r['side']} / {r['agent']}: " + ", ".join(b for b in bits if b))

    if args.json:
        p = Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nsumario -> {p}")


if __name__ == "__main__":
    main()
