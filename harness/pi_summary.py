#!/usr/bin/env python3
"""Resume o stream JSONL do `pi --mode json` (e do prime-agent, fork do pi
com o mesmo formato de eventos) no mesmo formato de topo que o
`claude -p --output-format json` devolve, para o jget do bench.sh ler os
mesmos campos (num_turns, duration_ms, total_cost_usd, is_error) em todos os
harnesses.

  pi_summary.py <events.jsonl> <duration_ms> <exit_code> [harness]

O duration_ms vem do bench.sh (relogio de parede a volta do pi) porque os
eventos do pi nao trazem timestamps por evento. Com timeout (exit 124) o
stream fica cortado a meio - resume-se o que houver, como no lado claude-code
um timeout da um JSON vazio.
"""
import json
import sys

path, duration_ms, exit_code = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
harness = sys.argv[4] if len(sys.argv) > 4 else "pi"

turns = 0
cost = 0.0
last_stop = None
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
            if t == "turn_end":
                turns += 1
            elif t == "message_end":
                msg = ev.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                c = ((msg.get("usage") or {}).get("cost") or {}).get("total")
                if isinstance(c, (int, float)):
                    cost += c
                last_stop = msg.get("stopReason")
                last_error = msg.get("errorMessage")
                texts = [b.get("text", "") for b in msg.get("content") or []
                         if isinstance(b, dict) and b.get("type") == "text"]
                if texts:
                    result_text = "\n".join(texts)
except OSError:
    pass

is_error = exit_code != 0 or last_stop in ("error", "aborted")
print(json.dumps({
    "type": "result",
    "harness": harness,
    "num_turns": turns,
    "duration_ms": duration_ms,
    "total_cost_usd": round(cost, 6),
    "is_error": is_error,
    "stop_reason": last_stop,
    "error": last_error,
    "result": result_text,
}))
