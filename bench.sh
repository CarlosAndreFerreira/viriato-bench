#!/usr/bin/env bash
# Lusitano Bench - corre a mesma tarefa na mesma harness com backends diferentes.
#
#   ./bench.sh                                   # tudo, k=3
#   SIDES=claude ./bench.sh                       # so o lado Claude (dias antes)
#   SIDES=qwen TASKS=a1-bugfix K=1 ./bench.sh     # smoke test rapido
#   AGENT=opencode SIDES=qwen ./bench.sh          # fase 2
#   AGENT=pi SIDES=qwen TASKS=v1-polygon K=1 ./bench.sh   # mesmo modelo, harness pi
#   AGENT=prime-agent SIDES=qwen K=1 ./bench.sh             # idem, harness prime-agent
#   AGENT=pi-sol SIDES=qwen K=1 ./bench.sh                  # pi + extensao SoL-Pi (NVIDIA)
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
# Primeiro k a correr. Serve para completar um batch existente sem apagar as
# runs que ja la estao (o run_one faz rm -rf do run dir de cada k): ex.
# BATCH_ID=<batch antigo> K_START=2 K=3 corre so as runs 2 e 3.
K_START="${K_START:-1}"
TIMEOUT_S="${TIMEOUT_S:-3000}"
TASKS="${TASKS:-v1-polygon v2-solar v3-viriato a1-bugfix}"
SIDES="${SIDES:-claude qwen}"
AGENT="${AGENT:-claude-code}"          # claude-code | opencode | pi | pi-sol | prime-agent
# So AGENT=pi|pi-sol|prime-agent: vai como reasoning_effort para o Ollama
# (supportsReasoningEffort=true em harness/*/models.json). Medido no Ollama
# 0.33.3 com o qwen3.8: reasoning_effort "none" desliga o raciocinio,
# low/medium/high/xhigh/max dao todos o mesmo, e sem o parametro o modelo ja
# raciocina. ATENCAO: PI_THINKING=off NAO desliga - o pi nesse caso nao envia
# parametro nenhum (capturado a 2026-09-24), e sem parametro o Ollama raciocina.
# O pi nao tem forma de enviar "none". O qwen3-coder nao tem modo de raciocinio.
PI_THINKING="${PI_THINKING:-medium}"

CLAUDE_MODEL="${CLAUDE_MODEL:-}"       # fixa explicitamente, ex: claude-opus-5
# Esforco do claude-code (claude --effort: low|medium|high|xhigh|max). Vazio =
# nao passar a flag, e o Claude Code envia output_config.effort "high"
# (capturado a 2026-09-25). O PROTOCOL 2 pre-registou "medium" e ate esta data
# nenhuma run o aplicou - ver RESULTS.md 6.5. Nome proprio do bench de
# proposito: CLAUDE_EFFORT tambem e lido pelo Claude Code.
CC_EFFORT="${CC_EFFORT:-}"
# Para isolar o efeito do tamanho do pedido do claude-code (RESULTS.md 3.3):
# CC_TOOLS restringe as ferramentas nativas (claude --tools, ex:
# "Read,Write,Edit,Bash,Glob,Grep") e CC_SYSTEM_PROMPT_FILE substitui o prompt
# de sistema (claude --system-prompt). Vazios = comportamento de origem.
CC_TOOLS="${CC_TOOLS:-}"
CC_SYSTEM_PROMPT_FILE="${CC_SYSTEM_PROMPT_FILE:-}"

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
# Pastas e logs arrumados por batch. Ate 2026-09-24 o nome era so
# agent-side-task-k: correr a mesma celula noutro batch fazia rm -rf da pasta
# e reescrevia os logs do batch anterior, e perderam-se assim as provas de seis
# celulas (RESULTS.md 6.2). As linhas do results.csv sobreviviam; o que estava
# por tras delas nao. Runs anteriores a esta data ficam na raiz de runs/ e logs/.
BATCH_DIR="${BATCH_ID//\//_}"
RUN_ROOT="$RUNS_DIR/$BATCH_DIR"
LOG_ROOT="$LOGS_DIR/$BATCH_DIR"
mkdir -p "$RUN_ROOT" "$LOG_ROOT"
echo "batch: $BATCH_ID"
[[ -n "$CC_EFFORT" && "$AGENT" == claude-code ]] && echo "claude-code --effort $CC_EFFORT"
[[ -n "$CC_TOOLS" && "$AGENT" == claude-code ]] && echo "claude-code --tools $CC_TOOLS"
[[ -n "$CC_SYSTEM_PROMPT_FILE" && "$AGENT" == claude-code ]] && echo "claude-code --system-prompt de $CC_SYSTEM_PROMPT_FILE"

# Le um campo de topo do JSON do agente. Usa jq se existir, senao python3.
jget() { # $1 = campo, $2 = ficheiro
  if command -v jq >/dev/null 2>&1; then
    jq -r --arg k "$1" 'if .[$k] == null then "NA" else .[$k] end' "$2" 2>/dev/null || echo NA
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

is_claude_side() {
  [[ "$1" == "claude" || "$1" == claude-* || "$1" == haiku* || "$1" == sonnet* || "$1" == opus* ]]
}

claude_model_for() {
  case "$1" in
    claude) echo "${CLAUDE_MODEL:-}" ;;
    haiku)  echo "claude-haiku-4-5" ;;
    sonnet) echo "claude-sonnet-4-6" ;;
    *)      echo "$1" ;;
  esac
}

local_model_for() {
  case "$1" in
    qwen)               echo "$QWEN_MODEL" ;;
    qwen3-coder)        echo "$QWEN_CODER_MODEL" ;;
    qwen3.8-flash-next) echo "$QWEN_FLASH_MODEL" ;;
    *)                  echo "$1" ;;
  esac
}

invoke_agent() {
  # $1 = side, $2 = prompt. cwd ja e o run dir.
  local side="$1" prompt="$2"
  case "$AGENT" in
    claude-code)
      if is_claude_side "$side"; then
        local model; model="$(claude_model_for "$side")"
        local mf=()
        [[ -n "$model" ]] && mf=(--model "$model")
        [[ -n "$CC_EFFORT" ]] && mf+=(--effort "$CC_EFFORT")
        [[ -n "$CC_TOOLS" ]] && mf+=(--tools "$CC_TOOLS")
        [[ -n "$CC_SYSTEM_PROMPT_FILE" ]] && mf+=(--system-prompt "$(cat "$CC_SYSTEM_PROMPT_FILE")")
        timeout "$TIMEOUT_S" claude -p "$prompt" "${mf[@]}" \
          --output-format json --allowedTools "$TOOLS" --permission-mode "$PERM_MODE"
      else
        local model; model="$(local_model_for "$side")"
        export ANTHROPIC_BASE_URL="$OLLAMA_URL"
        export ANTHROPIC_AUTH_TOKEN="ollama"
        export ANTHROPIC_API_KEY=""
        local ef=()
        [[ -n "$CC_EFFORT" ]] && ef=(--effort "$CC_EFFORT")
        [[ -n "$CC_TOOLS" ]] && ef+=(--tools "$CC_TOOLS")
        [[ -n "$CC_SYSTEM_PROMPT_FILE" ]] && ef+=(--system-prompt "$(cat "$CC_SYSTEM_PROMPT_FILE")")
        timeout "$TIMEOUT_S" claude -p "$prompt" --model "$model" "${ef[@]}" \
          --output-format json --allowedTools "$TOOLS" --permission-mode "$PERM_MODE"
      fi
      ;;
    opencode)
      [[ "$side" != "claude" ]] && export OPENAI_BASE_URL="$OLLAMA_URL/v1"
      timeout "$TIMEOUT_S" opencode run "$prompt"
      ;;
    pi|pi-sol|prime-agent)
      # pi-sol = o MESMO pi global + a extensao SoL-Pi da NVIDIA (harness/
      # sol-pi-src, commit fixado por harness/get-sol-pi.sh), com os 4
      # mecanismos ligados. Ablacao limpa contra AGENT=pi: so muda a extensao.
      # O SoL-Pi exige sessao persistente (falha com --no-session), por isso
      # grava-a em logs/, fora do run dir. O redutor de logs usa por omissao
      # um modelo remoto (openai-codex/gpt-5.6-luna) - aqui fica fixado ao
      # MESMO modelo do side, via sol-pi.json gerado por run.
      #
      # O prime-agent e um fork do pi: mesmas flags, mesmo stream JSON. Muda o
      # binario, a env var da config e as tools - o prime-agent so expoe uma,
      # `ipython` (le/edita ficheiros e corre comandos a partir de um kernel
      # persistente, e pode lancar sub-agentes com o mesmo modelo).
      #
      # Config propria do bench (harness/<agente>), nunca a do utilizador:
      # modelos Ollama sem samplingParams (fica o default do Ollama, como no
      # lado claude-code) e sem extensoes/skills/AGENTS.md/templates.
      # Assimetria a declarar: nenhum dos dois tem modo de permissoes, corre
      # tudo o que o modelo pede (o acceptEdits do claude-code ja deixa Bash).
      # O prime-agent corre SEM --autonomous-gate de proposito: um gate com o
      # verificador mostrava ao agente o criterio que os outros nao veem.
      local bin cfg_var tools cfg_dir="$ROOT/harness/$AGENT" extra=(--no-session)
      if [[ "$AGENT" == pi ]]; then
        bin=pi; cfg_var=PI_CODING_AGENT_DIR; tools=read,bash,edit,write,grep,find,ls
        extra+=(--no-approve)          # o prime-agent nao tem esta flag
      elif [[ "$AGENT" == pi-sol ]]; then
        local sol="$ROOT/harness/sol-pi-src/src/sol-pi/index.ts"
        [[ -f "$sol" ]] || { echo '{"is_error":true,"error":"falta o SoL-Pi: corre harness/get-sol-pi.sh"}'; return 1; }
        bin=pi; cfg_var=PI_CODING_AGENT_DIR
        tools=read,bash,edit,write,grep,find,ls,obs_recall,update_plan
        # --no-extensions nao bloqueia um -e explicito (pi --help).
        extra=(--no-approve -e "$sol" --session-dir "$PI_EVENTS_FILE.sessions")
      else
        bin=prime-agent; cfg_var=PRIME_AGENT_CODING_AGENT_DIR; tools=ipython
        extra+=(--offline)
      fi
      local provider model
      if is_claude_side "$side"; then
        [[ -n "${ANTHROPIC_API_KEY:-}" ]] || {
          echo "{\"is_error\":true,\"error\":\"$AGENT + lado claude precisa de ANTHROPIC_API_KEY (paga por token, fora da quota da subscricao)\"}"
          return 1
        }
        provider=anthropic
        model="$(claude_model_for "$side")"
        [[ -n "$model" ]] || { echo '{"is_error":true,"error":"fixa CLAUDE_MODEL"}'; return 1; }
      else
        provider=ollama
        model="$(local_model_for "$side")"
        [[ "$model" == *:* ]] || model="$model:latest"   # casa pelo id exato do models.json
      fi
      if [[ "$AGENT" == pi-sol ]]; then
        # Config por run: o sol-pi.json tem de apontar o redutor ao modelo
        # deste side, e o agent dir e onde o SoL-Pi o procura.
        cfg_dir="$PI_EVENTS_FILE.agent"
        rm -rf "$cfg_dir" "$PI_EVENTS_FILE.sessions"
        mkdir -p "$cfg_dir"
        cp "$ROOT/harness/pi-sol/models.json" "$ROOT/harness/pi-sol/settings.json" "$cfg_dir/"
        printf '{\n  "version": 1,\n  "actionFusion": true,\n  "observationPack": true,\n  "evidencePreservingReducer": true,\n  "evidencePreservingReducerProvider": "%s",\n  "evidencePreservingReducerModel": "%s",\n  "onlineContextCompact": true,\n  "cacheWriteReadRatio": 12.5\n}\n' \
          "$provider" "$model" > "$cfg_dir/sol-pi.json"
      fi
      local events="$PI_EVENTS_FILE" t0 rc
      t0=$(( $(date +%s%N) / 1000000 ))
      env "$cfg_var=$cfg_dir" PI_OFFLINE=1 PI_TELEMETRY=0 PRIME_AGENT_TELEMETRY=0 \
        timeout "$TIMEOUT_S" "$bin" -p "$prompt" --mode json \
          --provider "$provider" --model "$model" --thinking "$PI_THINKING" \
          --tools "$tools" \
          --no-extensions --no-skills --no-prompt-templates \
          --no-context-files "${extra[@]}" < /dev/null > "$events"   # sem isto o pi -p espera EOF num stdin que nao e tty
      rc=$?
      python3 "$ROOT/harness/pi_summary.py" "$events" "$(( $(date +%s%N) / 1000000 - t0 ))" "$rc" "$AGENT"
      return "$rc"
      ;;
    *)
      echo "{\"error\":\"AGENT desconhecido: $AGENT\"}"; return 1 ;;
  esac
}

run_one() {
  local side="$1" task="$2" k="$3"
  local rundir="$RUN_ROOT/$AGENT-$side-$task-$k"
  local log="$LOG_ROOT/$AGENT-$side-$task-$k.json"
  local prompt_file="$TASKS_DIR/$task/PROMPT.md"

  [[ -f "$prompt_file" ]] || { echo "  !! sem PROMPT.md para $task"; return; }

  rm -rf "$rundir"
  cp -r "$TASKS_DIR/$task/fixture" "$rundir"
  rm -f "$rundir/.keep"
  # Caches de corridas anteriores no fixture (ex: .pytest_cache/lastfailed
  # lista os testes que falham) dariam ao agente uma pista que o prompt nao da.
  find "$rundir" \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +

  local prompt; prompt="$(cat "$prompt_file")"
  local t0 t1 wall
  t0=$(date +%s)
  echo "==> $AGENT / $side / $task / run $k"

  # Subshell: as env vars do lado qwen nunca escapam para o lado claude.
  # $? tem de ser capturado logo a seguir - timeout (124), falha de auth e
  # quota esgotada saiam todos daqui, e sem isto ficavam indistinguiveis de
  # "o modelo respondeu e respondeu mal" (pass=0 por o verificador falhar).
  local agent_exit
  rm -rf "$log.events.jsonl" "$log.events.jsonl.agent" "$log.events.jsonl.sessions"
  ( cd "$rundir" && PI_EVENTS_FILE="$log.events.jsonl" invoke_agent "$side" "$prompt" ) > "$log" 2> "$log.stderr"
  agent_exit=$?

  # Esta maquina corre o Ollama com OLLAMA_KEEP_ALIVE=24h,
  # OLLAMA_MAX_LOADED_MODELS=3 e OLLAMA_NUM_PARALLEL=4. Com o contexto nativo
  # de 262144 tokens, cada modelo fica com ~39 GiB residentes e nunca sai da
  # memoria sozinho: a 3a tag local carregada levou a maquina a OOM a
  # 2026-09-22 17:59 e matou a sessao inteira (ver PROTOCOL 2.3). Descarregar
  # aqui mantem uma tag de cada vez em memoria.
  if ! is_claude_side "$side"; then
    local unload; unload="$(local_model_for "$side")"
    [[ "$unload" == *:* ]] || unload="$unload:latest"
    ollama stop "$unload" >/dev/null 2>&1
  fi

  local timeout_hit=0
  [[ "$agent_exit" -eq 124 ]] && timeout_hit=1

  t1=$(date +%s); wall=$((t1 - t0))

  local exit_tests=99
  if [[ -x "$TASKS_DIR/$task/score.sh" ]]; then
    ( cd "$rundir" && "$TASKS_DIR/$task/score.sh" ) >"$LOG_ROOT/$AGENT-$side-$task-$k.score" 2>&1
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
  is_claude_side "$side" || cost=0

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
  for k in $(seq "$K_START" "$K"); do
    for side in $SIDES; do
      run_one "$side" "$task" "$k"
    done
  done
done

echo
echo "batch $BATCH_ID completo"
echo "resultados crus -> $RESULTS"
echo "agrega com: python3 score.py   (usa so o batch mais recente por omissao)"
