#!/usr/bin/env bash
# Instala o SoL-Pi (NVIDIA) para AGENT=pi-sol, fixado a um commit.
# Nao toca no pi global: a extensao carrega-se com `pi -e` a partir daqui.
# Corre a suite do proprio SoL-Pi, como pede o agents-install.md deles.
set -euo pipefail
COMMIT=1559b5cb12c72da4a485bc50fe326586b216fb19   # 2026-09-22
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/sol-pi-src"
[[ -d "$DIR/.git" ]] || git clone -q https://github.com/NVlabs/SoL-Pi "$DIR"
git -C "$DIR" fetch -q origin
git -C "$DIR" checkout -q "$COMMIT"
( cd "$DIR" && npm ci --ignore-scripts && npm run check )
echo "SoL-Pi $COMMIT pronto em $DIR"
