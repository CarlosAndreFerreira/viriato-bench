#!/usr/bin/env python3
"""Implementacao de referencia do V3.

NAO faz parte da tarefa e NAO pode ser copiada para tasks/v3-viriato/fixture/.
Existe por uma unica razao: provar que as constraints de tasks/v3-viriato
sao satisfaziveis em simultaneo. Um checker que ninguem consegue passar nao
mede nada.

    python3 verify/reference_maze.py            # imprime o labirinto
    make check-reference                        # corre o verifier contra isto
"""
from __future__ import annotations

import random

ROWS, COLS = 36, 28
CORRIDOR_ROWS = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
CORRIDOR_COLS = [1, 4, 7, 10, 13, 14, 17, 20, 23, 26]
CASTRUM_ROWS = range(15, 19)
CASTRUM_COLS = range(11, 17)
TUNNEL_ROW = 22


def generate_maze(seed: int) -> list[list[int]]:
    rng = random.Random(seed)
    g = [[1] * COLS for _ in range(ROWS)]

    for r in CORRIDOR_ROWS:
        for c in range(1, COLS - 1):
            g[r][c] = 0
    for c in CORRIDOR_COLS:
        for r in range(1, ROWS - 1):
            g[r][c] = 0

    # anel de corredor a volta do castrum
    for c in range(10, 18):
        g[14][c] = 0
        g[19][c] = 0
    for r in range(14, 20):
        g[r][10] = 0
        g[r][17] = 0

    # segmentos verticais extra, em pares simetricos, sempre de linha a linha
    pairs = [(c, COLS - 1 - c) for c in range(2, COLS // 2) if c not in CORRIDOR_COLS]
    for c, mc in rng.sample(pairs, k=min(3, len(pairs))):
        i = rng.randrange(len(CORRIDOR_ROWS) - 1)
        a, b = CORRIDOR_ROWS[i], CORRIDOR_ROWS[i + 1]
        for r in range(a, b + 1):
            g[r][c] = 0
            g[r][mc] = 0

    # castrum solido, reescrito por ultimo
    for r in CASTRUM_ROWS:
        for c in CASTRUM_COLS:
            g[r][c] = 1

    # bordadura e tunel unico
    for c in range(COLS):
        g[0][c] = g[ROWS - 1][c] = 1
    for r in range(ROWS):
        g[r][0] = g[r][COLS - 1] = 1
    g[TUNNEL_ROW][0] = g[TUNNEL_ROW][COLS - 1] = 0
    return g


def render(grid: list[list[int]]) -> str:
    return "\n".join("".join("#" if v else " " for v in row) for row in grid)


if __name__ == "__main__":
    print(render(generate_maze(1)))
