#!/usr/bin/env bash
# Lusitano Bench - corre a mesma tarefa na mesma harness com backends diferentes.
#
#   ./bench.sh                                   # tudo, k=3
#   SIDES=claude ./bench.sh                       # so o lado Claude (dias antes)
#   SIDES=qwen TASKS=a1-bugfix K=1 ./bench.sh     # smoke test rapido
#   AGENT=opencode SIDES=qwen ./bench.sh          # fase 2
#   BATCH_ID=fase2-run2 SIDES=qwen ./bench.sh     # nomeia o batch (2a+ passagem;
#                                                  # score.py so agrega o mais recente)
#   SIDES="qwen qwen3-coder qwen3.8-flash-next" K=3 ./bench.sh   # varios modelos locais
#
# Requisitos: o CLI do agente, pytest, timeout (coreutils). jq e opcional.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASKS_DIR="$ROOT/tasks"
RUNS_DIR="$ROOT/runs"
LOGS_DIR="$ROOT/logs"
RESULTS="$ROOT/results.csv"

K="${K:-3}"
TIMEOUT_S="${TIMEOUT_S:-3000}"
TASKS="${TASKS:-v1-polygon v2-solar v3-viriato a1-bugfix}"
SIDES="${SIDES:-claude qwen}"
AGENT="${AGENT:-claude-code}"          # claude-code | opencode | pi | prime-agent

CLAUDE_MODEL="${CLAUDE_MODEL:-}"       # fixa explicitamente, ex: claude-opus-5

# Um "side" local por modelo a comparar. Cada um mapeia para uma tag do
# Ollama; sobrepoe-se com a env var respetiva se quiseres testar outra tag.
# Um side desconhecido (fora deste mapa e diferente de "claude") e tratado
# como a propria tag do Ollama - nao e preciso editar o script para testar
# um modelo novo, so acrescentar o nome a SIDES.
QWEN_MODEL="${QWEN_MODEL:-qwen3.8}"
QWEN_CODER_MODEL="${QWEN_CODER_MODEL:-qwen3-coder:30b}"
QWEN_FLASH_MODEL="${QWEN_FLASH_MODEL:-qwen3.8-flash-next:latest}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
TOOLS="${TOOLS:-Read,Write,Edit,Bash,Glob,Grep}"
PERM_MODE="${PERM_MODE:-acceptEdits}"  # IDENTICO nos dois lados

# Um id por invocacao do bench.sh. results.csv e append-only e a Fase 2 do
# README convida a correr o lado qwen "quantas vezes quiseres" - sem isto,
# uma segunda passagem mistura silenciosamente runs antigas e novas no mesmo
# denominador do pass@1. Sobrepoe-se para dar nome a um batch (ex: "fase2-2").
BATCH_ID="${BATCH_ID:-$(date +%Y%m%dT%H%M%S)-$$}"

command -v timeout >/dev/null || { echo "falta timeout (coreutils)"; exit 1; }
mkdir -p "$RUNS_DIR" "$LOGS_DIR"
echo "batch: $BATCH_ID"

# Le um campo de topo do JSON do agente. Usa jq se existir, senao python3.
jget() { # $1 = campo, $2 = ficheiro
  if command -v jq >/dev/null 2>&1; then
    jq -r --arg k "$1" '.[$k] // "NA"' "$2" 2>/dev/null || echo NA
  else
    python3 - "$1" "$2" <<'PY' 2>/dev/null || echo NA
import json, sys
key, path = sys.argv[1], sys.argv[2]
try:
    with open(path, encoding="utf-8") as fh:
        v = json.load(fh).get(key, "NA")
except Exception:
    v = "NA"
print("NA" if v is None else v)
PY
  fi
}

if [[ ! -f "$RESULTS" ]]; then
  echo "ts,batch_id,agent,side,task,k,pass,skip,exit_tests,agent_exit,timeout_hit,num_turns,duration_ms,cost_usd,is_error,wall_s" > "$RESULTS"
fi

invoke_agent() {
  # $1 = side, $2 = prompt. cwd ja e o run dir.
  local side="$1" prompt="$2"
  case "$AGENT" in
    claude-code)
      if [[ "$side" == "claude" ]]; then
        local mf=()
        [[ -n "$CLAUDE_MODEL" ]] && mf=(--model "$CLAUDE_MODEL")
        timeout "$TIMEOUT_S" claude -p "$prompt" "${mf[@]}" \
          --output-format json --allowedTools "$TOOLS" --permission-mode "$PERM_MODE"
      else
        local model
        case "$side" in
          qwen)               model="$QWEN_MODEL" ;;
          qwen3-coder)        model="$QWEN_CODER_MODEL" ;;
          qwen3.8-flash-next) model="$QWEN_FLASH_MODEL" ;;
          *)                  model="$side" ;;
        esac
        export ANTHROPIC_BASE_URL="$OLLAMA_URL"
        export ANTHROPIC_AUTH_TOKEN="ollama"
        export ANTHROPIC_API_KEY=""
        timeout "$TIMEOUT_S" claude -p "$prompt" --model "$model" \
          --output-format json --allowedTools "$TOOLS" --permission-mode "$PERM_MODE"
      fi
      ;;
    opencode)
      [[ "$side" != "claude" ]] && export OPENAI_BASE_URL="$OLLAMA_URL/v1"
      timeout "$TIMEOUT_S" opencode run "$prompt"
      ;;
    pi|prime-agent)
      echo "{\"note\":\"$AGENT ainda nao ligado; ver README, Fase 2\"}"
      return 1
      ;;
    *)
      echo "{\"error\":\"AGENT desconhecido: $AGENT\"}"; return 1 ;;
  esac
}

run_one() {
  local side="$1" task="$2" k="$3"
  local rundir="$RUNS_DIR/$AGENT-$side-$task-$k"
  local log="$LOGS_DIR/$AGENT-$side-$task-$k.json"
  local prompt_file="$TASKS_DIR/$task/PROMPT.md"

  [[ -f "$prompt_file" ]] || { echo "  !! sem PROMPT.md para $task"; return; }

  rm -rf "$rundir"
  cp -r "$TASKS_DIR/$task/fixture" "$rundir"
  rm -f "$rundir/.keep"

  local prompt; prompt="$(cat "$prompt_file")"
  local t0 t1 wall
  t0=$(date +%s)
  echo "==> $AGENT / $side / $task / run $k"

  # Subshell: as env vars do lado qwen nunca escapam para o lado claude.
  # $? tem de ser capturado logo a seguir - timeout (124), falha de auth e
  # quota esgotada saiam todos daqui, e sem isto ficavam indistinguiveis de
  # "o modelo respondeu e respondeu mal" (pass=0 por o verificador falhar).
  local agent_exit
  ( cd "$rundir" && invoke_agent "$side" "$prompt" ) > "$log" 2> "$log.stderr"
  agent_exit=$?

  local timeout_hit=0
  [[ "$agent_exit" -eq 124 ]] && timeout_hit=1

  t1=$(date +%s); wall=$((t1 - t0))

  local exit_tests=99
  if [[ -x "$TASKS_DIR/$task/score.sh" ]]; then
    ( cd "$rundir" && "$TASKS_DIR/$task/score.sh" ) >"$LOGS_DIR/$AGENT-$side-$task-$k.score" 2>&1
    exit_tests=$?
  fi
  local passed=0 skipped=0
  case "$exit_tests" in
    0) passed=1 ;;
    2) skipped=1 ;;
  esac

  local turns dur cost err
  turns=$(jget num_turns      "$log")
  dur=$(  jget duration_ms    "$log")
  cost=$( jget total_cost_usd "$log")
  err=$(  jget is_error       "$log")

  # O CLI reporta um total_cost_usd para QUALQUER modelo, incluindo um local
  # nao reconhecido - com costBasis "unknown" no JSON completo (nao exposto
  # por --output-format json), calculado por uma tarifa de fallback que nao
  # se aplica a um modelo a correr de graca no teu proprio hardware. Gravar
  # isso ao pe da letra contradiz "custo marginal zero" (README, Fase 2). O
  # custo real do lado local e o que o monitor.py mede (energia), nao isto.
  [[ "$side" != "claude" ]] && cost=0

  echo "$(date -Is),$BATCH_ID,$AGENT,$side,$task,$k,$passed,$skipped,$exit_tests,$agent_exit,$timeout_hit,$turns,$dur,$cost,$err,$wall" >> "$RESULTS"
  if [[ "$timeout_hit" == 1 ]]; then
    echo "    !! TIMEOUT (${TIMEOUT_S}s) - o agente nao respondeu a tempo, nao e o mesmo que 'respondeu errado'  wall=${wall}s"
  elif [[ "$agent_exit" != 0 ]]; then
    echo "    !! agente saiu com exit=$agent_exit (crash/auth/quota?) antes do verificador correr  wall=${wall}s"
  elif [[ "$skipped" == 1 ]]; then
    echo "    SKIP (verificador indisponivel)  wall=${wall}s"
  else
    echo "    pass=$passed  turns=$turns  wall=${wall}s  cost=$cost"
  fi
}

for task in $TASKS; do
  for k in $(seq 1 "$K"); do
    for side in $SIDES; do
      run_one "$side" "$task" "$k"
    done
  done
done

echo
echo "batch $BATCH_ID completo"
echo "resultados crus -> $RESULTS"
echo "agrega com: python3 score.py   (usa so o batch mais recente por omissao)"
