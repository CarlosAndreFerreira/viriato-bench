#!/usr/bin/env python3
"""Resume o stream JSONL do `opencode run --format json` no mesmo formato de
topo que o `claude -p --output-format json` (ver pi_summary.py), para o jget
do bench.sh ler num_turns, duration_ms, total_cost_usd e is_error.

  oc_summary.py <events.jsonl> <duration_ms> <exit_code>

Um turno = um evento step_finish (um pedido ao modelo). Conta tambem as
chamadas a ferramentas e os caracteres de raciocinio, para distinguir "o
modelo pensou sem agir" de "agiu e errou".
"""
import json
import sys

path, duration_ms, exit_code = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

turns = tool_calls = reasoning_chars = 0
cost = 0.0
last_reason = None
last_error = None
result_text = None

try:
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            t = ev.get("type")
            part = ev.get("part") or {}
            if t == "step_finish":
                turns += 1
                last_reason = part.get("reason")
                c = part.get("cost")
                if isinstance(c, (int, float)):
                    cost += c
            elif t == "tool_use":
                tool_calls += 1
            elif t == "reasoning":
                reasoning_chars += len(part.get("text") or "")
            elif t == "text":
                result_text = part.get("text")
            elif t == "error":
                last_error = ev.get("error") or part
except OSError:
    pass

print(json.dumps({
    "type": "result",
    "harness": "opencode",
    "num_turns": turns,
    "tool_calls": tool_calls,
    "reasoning_chars": reasoning_chars,
    "duration_ms": duration_ms,
    "total_cost_usd": round(cost, 6),
    "is_error": exit_code != 0 or last_error is not None,
    "stop_reason": last_reason,
    "error": last_error,
    "result": result_text,
}, default=str))
