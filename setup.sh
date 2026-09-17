#!/usr/bin/env bash
# Verifica o ambiente antes da primeira run. Nao instala nada sem avisar.
set -uo pipefail
ok=0; warn=0

chk() { # nome, comando
  if command -v "$2" >/dev/null 2>&1; then
    printf '  [ok]   %-14s %s\n' "$1" "$(command -v "$2")"; ok=$((ok+1))
  else
    printf '  [FALTA] %-13s instala com: %s\n' "$1" "$3"; warn=$((warn+1))
  fi
}

echo "Lusitano Bench - verificacao de ambiente"
echo
chk jq      jq      "sudo apt install jq"
chk timeout timeout "sudo apt install coreutils"
chk claude  claude  "ver docs do Claude Code"
chk ollama  ollama  "https://ollama.com"

if python3 -c "import pytest" 2>/dev/null; then
  printf '  [ok]   %-14s %s\n' pytest "$(python3 -c 'import pytest;print(pytest.__version__)')"
else
  printf '  [FALTA] %-13s pip install --break-system-packages pytest\n' pytest; warn=$((warn+1))
fi

if python3 -c "import playwright" 2>/dev/null; then
  printf '  [ok]   %-14s instalado\n' playwright
else
  printf '  [aviso] %-13s V1 e V2 vao dar SKIP. Ver README seccao 0.\n' playwright
fi

echo
echo "Ollama:"
if command -v ollama >/dev/null 2>&1; then ollama list 2>/dev/null | head -6; fi

echo
chmod +x bench.sh tasks/*/score.sh 2>/dev/null
echo "Permissoes de execucao aplicadas."
[[ $warn -gt 0 ]] && echo "$warn item(s) em falta acima." || echo "Ambiente pronto."
