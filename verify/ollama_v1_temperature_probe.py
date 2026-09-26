#!/usr/bin/env python3
"""Prova se o Ollama aplica a temperatura do Modelfile em cada endpoint.

  python3 verify/ollama_v1_temperature_probe.py [tag] [n]

Faz o mesmo pedido curto n vezes (raciocinio desligado, 60 tokens) por
quatro caminhos e conta as respostas distintas:

  native            /api/chat sem opcoes           -> usa o Modelfile
  v1                /v1/chat/completions sem temp  -> o que pi/opencode enviam
  v1+temp           /v1/chat/completions com a temperatura do Modelfile
  messages          /v1/messages sem temp          -> o que o claude-code envia

Se o Modelfile e respeitado, "v1" parece-se com "native" e "v1+temp". Medido
a 2026-09-26 no Ollama 0.33.3 (RESULTS.md 6.7): nao e.

ATENCAO: carrega a tag (o qwen3.8 ocupa ~40 GiB). Descarrega no fim.
"""
import json
import subprocess
import sys
import urllib.request

TAG = sys.argv[1] if len(sys.argv) > 1 else "qwen3.8-t02:latest"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
URL = "http://localhost:11434"
MSG = [{"role": "user", "content": "Invent a name for a new fruit and describe its taste in one sentence."}]


def modelfile_temperature():
    out = subprocess.run(["ollama", "show", TAG, "--parameters"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[0] == "temperature":
            return float(parts[1])
    return None


def call(path, body):
    req = urllib.request.Request(URL + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "x-api-key": "x",
                                  "anthropic-version": "2023-06-01"})
    return json.load(urllib.request.urlopen(req))


def text(path, r):
    if path == "/api/chat":
        return r["message"]["content"]
    if path == "/v1/messages":
        return "".join(c.get("text", "") for c in r["content"] if c.get("type") == "text")
    return r["choices"][0]["message"]["content"] or ""


def main():
    temp = modelfile_temperature()
    arms = {
        "native": ("/api/chat", {"model": TAG, "stream": False, "think": False, "messages": MSG,
                                 "options": {"num_predict": 60}}),
        "v1": ("/v1/chat/completions", {"model": TAG, "stream": False, "max_tokens": 60,
                                        "reasoning_effort": "none", "messages": MSG}),
        "v1+temp": ("/v1/chat/completions", {"model": TAG, "stream": False, "max_tokens": 60,
                                             "reasoning_effort": "none", "messages": MSG,
                                             "temperature": temp}),
        "messages": ("/v1/messages", {"model": TAG, "stream": False, "max_tokens": 60,
                                      "thinking": {"type": "disabled"}, "messages": MSG}),
    }
    print(f"tag={TAG} temperature do Modelfile={temp} n={N}")
    seen = {}
    try:
        for name, (path, body) in arms.items():
            outs = [text(path, call(path, body)).strip().replace("\n", " ")[:100] for _ in range(N)]
            seen[name] = set(outs)
            print(f"\n{name:9s} {path:22s} distintas={len(set(outs))}/{N}")
            for o in sorted(set(outs)):
                print("    ", o)
        ref = seen["native"]
        print("\nfrases em comum com 'native':",
              {k: len(v & ref) for k, v in seen.items() if k != "native"})
    finally:
        subprocess.run(["ollama", "stop", TAG])


if __name__ == "__main__":
    main()
