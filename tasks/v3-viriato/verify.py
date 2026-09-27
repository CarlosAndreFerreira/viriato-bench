#!/usr/bin/env python3
"""Verifica maze.py contra as constraints do SRS do Viriato's Maze.

Corre a partir do run dir. Exit 0 = pass. Sem dependencias externas.
"""
from __future__ import annotations

import importlib.util
import sys
from collections import deque
from pathlib import Path

ROWS, COLS = 36, 28
CASTRUM_COLS = range(11, 17)   # 6 colunas
CASTRUM_ROWS = range(15, 19)   # 4 linhas
SEEDS = [1, 7, 42, 1234]

fails: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)


def load():
    p = Path("maze.py")
    if not p.exists():
        print("FAIL: maze.py nao existe na raiz do run dir")
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("maze", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["maze"] = mod
    spec.loader.exec_module(mod)
    return mod


def check_grid(grid, seed: int) -> None:
    tag = f"[seed {seed}]"

    if not isinstance(grid, list) or len(grid) != ROWS:
        fail(f"{tag} grelha tem {len(grid) if hasattr(grid,'__len__') else '?'} linhas, esperava {ROWS}")
        return
    for r, row in enumerate(grid):
        if not hasattr(row, "__len__") or len(row) != COLS:
            fail(f"{tag} linha {r} tem largura errada")
            return
    vals = {v for row in grid for v in row}
    if not vals <= {0, 1}:
        fail(f"{tag} valores fora de 0/1: {vals - {0, 1}}")
        return

    # (3) simetria horizontal
    asym = [(r, c) for r in range(ROWS) for c in range(COLS)
            if grid[r][c] != grid[r][COLS - 1 - c]]
    if asym:
        fail(f"{tag} simetria horizontal falha em {len(asym)} celulas, ex: {asym[:3]}")

    # (7) tunel: linhas em que col 0 e col 27 sao corredor
    tunnel_rows = [r for r in range(ROWS) if grid[r][0] == 0 and grid[r][COLS - 1] == 0]
    if len(tunnel_rows) != 1:
        fail(f"{tag} esperava exatamente 1 linha de tunel, encontrei {len(tunnel_rows)}: {tunnel_rows}")
    for r in tunnel_rows:
        if r in CASTRUM_ROWS:
            fail(f"{tag} tunel na linha {r} atravessa o castrum")

    # (2) bordadura
    for c in range(COLS):
        if grid[0][c] != 1 or grid[ROWS - 1][c] != 1:
            fail(f"{tag} bordadura horizontal aberta na coluna {c}")
            break
    for r in range(ROWS):
        if r in tunnel_rows:
            continue
        if grid[r][0] != 1 or grid[r][COLS - 1] != 1:
            fail(f"{tag} bordadura vertical aberta na linha {r}")
            break

    # (6) castrum
    bad = [(r, c) for r in CASTRUM_ROWS for c in CASTRUM_COLS if grid[r][c] != 1]
    if bad:
        fail(f"{tag} castrum 6x4 (linhas 15-18, colunas 11-16) nao e solido: {len(bad)} buracos")
    ring = []
    for c in range(10, 18):
        ring += [(14, c), (19, c)]
    for r in CASTRUM_ROWS:
        ring += [(r, 10), (r, 17)]
    open_ring = [(r, c) for r, c in ring
                 if 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] == 0]
    if not open_ring:
        fail(f"{tag} castrum nao esta rodeado de corredor")

    corridors = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == 0]
    if not corridors:
        fail(f"{tag} sem corredores")
        return

    # (4) sem dead ends
    def neigh(r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] == 0:
                yield nr, nc
        # wrap-around do tunel
        if c == 0 and grid[r][COLS - 1] == 0 and r in tunnel_rows:
            yield r, COLS - 1
        if c == COLS - 1 and grid[r][0] == 0 and r in tunnel_rows:
            yield r, 0

    dead = [(r, c) for r, c in corridors if len(list(neigh(r, c))) < 2]
    if dead:
        fail(f"{tag} {len(dead)} dead ends, ex: {dead[:5]}")

    # (5) componente conexo unico
    seen = {corridors[0]}
    q = deque([corridors[0]])
    while q:
        cur = q.popleft()
        for nxt in neigh(*cur):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    if len(seen) != len(corridors):
        fail(f"{tag} corredores desconexos: {len(seen)}/{len(corridors)} alcancaveis")

    # (8) densidade
    dens = len(corridors) / (ROWS * COLS)
    if not 0.35 <= dens <= 0.60:
        fail(f"{tag} densidade de corredor {dens:.2%} fora de [35%, 60%]")


def main() -> int:
    mod = load()
    if not hasattr(mod, "generate_maze"):
        print("FAIL: maze.py nao expoe generate_maze")
        return 1

    grids = {}
    for seed in SEEDS:
        try:
            grids[seed] = mod.generate_maze(seed)
        except Exception as exc:  # noqa: BLE001
            fail(f"[seed {seed}] generate_maze rebentou: {exc!r}")
            continue
        check_grid(grids[seed], seed)

    # (9) determinismo e variedade
    for seed, g in grids.items():
        try:
            if mod.generate_maze(seed) != g:
                fail(f"[seed {seed}] nao e determinista")
        except Exception as exc:  # noqa: BLE001
            fail(f"[seed {seed}] segunda chamada rebentou: {exc!r}")
    uniq = {repr(g) for g in grids.values()}
    if len(grids) > 1 and len(uniq) < 2:
        fail("seeds diferentes produzem a mesma grelha")

    # render
    # Ate 2026-09-27 os dois casos do else davam "nao expoe render()", mesmo
    # com render() definido quando todas as seeds rebentavam (RESULTS.md 6.5).
    # So a mensagem mudou: continua a ser um problema, e o veredito e o mesmo.
    if not hasattr(mod, "render"):
        fail("maze.py nao expoe render()")
    elif not grids:
        fail("render() nao testado: nenhuma seed gerou grelha")
    else:
        try:
            out = mod.render(next(iter(grids.values())))
            if not isinstance(out, str) or len(out.splitlines()) != ROWS:
                fail("render() nao devolve 36 linhas de texto")
        except Exception as exc:  # noqa: BLE001
            fail(f"render() rebentou: {exc!r}")

    if fails:
        print(f"FAIL ({len(fails)} problemas):")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS: todas as constraints do SRS verificadas em", len(SEEDS), "seeds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
