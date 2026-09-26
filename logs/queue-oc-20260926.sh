#!/usr/bin/env bash
# Fila opencode: temperatura 1 vs 0.2, mesmo qwen3.8, temperatura enviada explicitamente.
cd /home/carlos-andr-ferreira/viriato-bench
guard() {
  for m in $(ollama ps | awk 'NR>1{print $1}'); do ollama stop "$m"; done
  sleep 3
  local avail; avail=$(free -g | awk '/^Mem:/{print $7}')
  echo "[guard $(date +%T)] avail=${avail}G carregados=[$(ollama ps | awk 'NR>1{print $1}' | xargs)]"
  (( avail >= 60 )) || { echo "[guard] RAM insuficiente, abortar"; exit 1; }
}
python3 monitor.py --out power-oc-t02-20260926.csv >/dev/null 2>&1 &
MON=$!
guard
# 1) smoke: a1, K=1, so t02
AGENT=opencode SIDES=qwen3.8-t02 TASKS=a1-bugfix K=1 BATCH_ID=oc-smoke ./bench.sh
guard
# 2) experiencia principal: braços intercalados por tarefa, K=3
for task in v1-polygon v2-solar; do
  for side in qwen3.8-t02 qwen; do
    AGENT=opencode SIDES=$side TASKS=$task K=3 BATCH_ID=oc-temp-k3 ./bench.sh
    guard
  done
done
kill $MON 2>/dev/null
echo "FILA OC TERMINADA $(date)"
