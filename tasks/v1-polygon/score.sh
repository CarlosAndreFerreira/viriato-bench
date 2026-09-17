#!/usr/bin/env bash
# Executado com cwd = run dir. Exit 0 pass, 1 fail, 2 skip.
set -uo pipefail
TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$TASK_DIR/verify.py"
