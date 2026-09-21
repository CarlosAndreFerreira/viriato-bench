#!/usr/bin/env bash
# Executado com cwd = run dir. Exit 0 pass, 1 fail.
#
# a1 nao tem noção de SKIP legitima (nao depende de Playwright). O pytest
# devolve exit 2 tambem em erro de colecao (ex: syntax error introduzido pelo
# agente) - se deixassemos esse codigo passar, o bench.sh interpretava-o como
# o SKIP=2 do browser.py e a run desaparecia do denominador do pass@1 em vez
# de contar como falha. Por isso normalizamos: so 0 e pass, tudo o resto e 1.
#
# O prompt proibe mexer em tests/, mas isso nao se verifica pedindo. Antes de
# correr, repomos tests/ e conftest.py a partir do fixture original: um agente
# que relaxou ou apagou testes corre contra os originais e falha. A alteracao
# fica registada no .score para se ver no log que houve tentativa.
set -uo pipefail
FIXTURE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/fixture"

tampered=0
for p in tests conftest.py; do
  if ! diff -rq -x __pycache__ -x .pytest_cache "$FIXTURE/$p" "$p" >/dev/null 2>&1; then
    echo "!! $p alterado pelo agente - reposto a partir do fixture:"
    diff -ru -x __pycache__ -x .pytest_cache "$FIXTURE/$p" "$p"
    tampered=1
  fi
  rm -rf "$p"
  cp -r "$FIXTURE/$p" "$p"
done
find tests \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
rm -rf .pytest_cache

python3 -m pytest -q -p no:cacheprovider tests
code=$?
[[ "$tampered" -eq 1 ]] && echo "!! testes alterados pelo agente (ver diff acima) - avaliado contra os originais"
[[ "$code" -eq 0 ]] && exit 0
exit 1
