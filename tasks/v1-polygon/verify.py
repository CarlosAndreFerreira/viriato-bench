#!/usr/bin/env python3
"""Verifica o V1: bolas dentro de um nonagono em rotacao.

Correcao objetiva, sem julgar estetica. Corre a partir do run dir.
Exit 0 pass, 1 fail, 2 skip (playwright em falta).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "verify"))
from browser import has_bench, page_for  # noqa: E402

N_SIDES = 9
N_BALLS = 13
BALL_R = 14.0
PERIOD = 7.0
SAMPLES = 60          # amostras de estado
DT = 0.05             # segundos por passo
TOL_WALL = 1.5        # px de folga numerica
TOL_OVERLAP = 1.0     # px de interpenetracao tolerada

fails: list[str] = []


def inside_polygon(bx, by, st) -> float:
    """Distancia minima da borda da bola a parede. Negativo = fora."""
    poly = st["poly"]
    cx, cy, R, ang, n = poly["cx"], poly["cy"], poly["radius"], poly["angle"], int(poly["n"])
    apothem = R * math.cos(math.pi / n)
    worst = float("inf")
    for i in range(n):
        theta = ang + 2 * math.pi * i / n + math.pi / n
        nx, ny = math.cos(theta), math.sin(theta)
        dist = apothem - ((bx - cx) * nx + (by - cy) * ny)
        worst = min(worst, dist)
    return worst - BALL_R


def main() -> int:
    with page_for(frames_dir="_frames") as (page, errors):
        if not has_bench(page):
            print("FAIL: window.__bench nao existe (contrato do prompt nao cumprido)")
            return 1

        st0 = page.evaluate("() => window.__bench.getState()")
        if not isinstance(st0, dict) or "balls" not in st0 or "poly" not in st0:
            print("FAIL: getState() nao respeita o formato do contrato")
            return 1

        poly = st0["poly"]
        if int(poly.get("n", 0)) != N_SIDES:
            fails.append(f"poly.n = {poly.get('n')}, esperava {N_SIDES}")
        if abs(float(poly.get("periodSec", 0)) - PERIOD) > 0.01:
            fails.append(f"periodSec = {poly.get('periodSec')}, esperava {PERIOD}")
        if len(st0["balls"]) != N_BALLS:
            fails.append(f"{len(st0['balls'])} bolas, esperava {N_BALLS}")
        ids = sorted(b.get("id") for b in st0["balls"])
        if ids != list(range(len(st0["balls"]))):
            fails.append(f"ids das bolas nao sao 0..{N_BALLS - 1}: {ids}")

        has_step = page.evaluate("() => typeof window.__bench.step === 'function'")
        if not has_step:
            fails.append("window.__bench.step(dt) em falta; caio para tempo real")

        angles = []
        times = []
        escapes = 0
        overlaps = 0
        worst_escape = 0.0
        worst_overlap = 0.0

        for _ in range(SAMPLES):
            if has_step:
                page.evaluate(f"() => window.__bench.step({DT})")
            else:
                page.wait_for_timeout(int(DT * 1000))
            st = page.evaluate("() => window.__bench.getState()")
            times.append(float(st["t"]))
            angles.append(float(st["poly"]["angle"]))

            balls = st["balls"]
            for b in balls:
                clearance = inside_polygon(float(b["x"]), float(b["y"]), st)
                if clearance < -TOL_WALL:
                    escapes += 1
                    worst_escape = min(worst_escape, clearance)
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    dx = float(balls[i]["x"]) - float(balls[j]["x"])
                    dy = float(balls[i]["y"]) - float(balls[j]["y"])
                    pen = 2 * BALL_R - math.hypot(dx, dy)
                    if pen > TOL_OVERLAP:
                        overlaps += 1
                        worst_overlap = max(worst_overlap, pen)

        if escapes:
            fails.append(f"{escapes} amostras com bola fora do poligono (pior: {worst_escape:.1f} px)")
        if overlaps:
            fails.append(f"{overlaps} amostras com bolas sobrepostas (pior: {worst_overlap:.1f} px)")

        # rotacao: 360 graus em PERIOD segundos
        if len(angles) > 2:
            dtheta = 0.0
            for a, b in zip(angles, angles[1:]):
                d = (b - a + math.pi) % (2 * math.pi) - math.pi
                dtheta += abs(d)
            elapsed = times[-1] - times[0]
            if elapsed > 0.1:
                measured = 2 * math.pi / (dtheta / elapsed)
                if abs(measured - PERIOD) / PERIOD > 0.10:
                    fails.append(f"periodo medido {measured:.2f}s, esperava {PERIOD}s (+/-10%)")
            else:
                fails.append("tempo nao avanca: simulacao parada ou t nao e atualizado")

        # movimento real: as bolas tem de se ter mexido
        st1 = page.evaluate("() => window.__bench.getState()")
        moved = max(
            math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))
            for a, b in zip(st0["balls"], st1["balls"])
        ) if st1.get("balls") else 0.0
        if moved < 5:
            fails.append("nenhuma bola se moveu: animacao inexistente")

        if errors:
            fails.append(f"{len(errors)} erros de JavaScript, ex: {errors[0][:120]}")

    if fails:
        print(f"FAIL ({len(fails)} problemas):")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS: fisica, contencao, nao-sobreposicao e periodo de rotacao verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
