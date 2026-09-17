#!/usr/bin/env bash
# Executado com cwd = run dir. Exit 0 pass, 1 fail.
#
# a1 nao tem noção de SKIP legitima (nao depende de Playwright). O pytest
# devolve exit 2 tambem em erro de colecao (ex: syntax error introduzido pelo
# agente) - se deixassemos esse codigo passar, o bench.sh interpretava-o como
# o SKIP=2 do browser.py e a run desaparecia do denominador do pass@1 em vez
# de contar como falha. Por isso normalizamos: so 0 e pass, tudo o resto e 1.
set -uo pipefail
python3 -m pytest -q tests
code=$?
[[ "$code" -eq 0 ]] && exit 0
exit 1
