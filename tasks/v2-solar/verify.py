#!/usr/bin/env python3
"""Verifica o V2: sistema solar + janelas da missao a Marte.

Este e o verificador que separa "bonito" de "correto". Corre a partir do run
dir. Exit 0 pass, 1 fail, 2 skip (playwright em falta).

O contrato antigo so expunha bodies{auRadius,periodDays} e mission{...} com
os numeros auto-declarados pela pagina, mais getState() com a posicao actual
da nave. Isso e verificavel a maquina, mas uma pagina podia escrever os
numeros certos no contrato sem simular fisica nenhuma - o unico teste
dinamico era "a nave mexeu-se", que uma posicao a avancar linearmente tambem
passa. Confirmado empiricamente: um index.html de 30 linhas so com o objecto
do contrato, sem orbitas nem transferencia de Hohmann nenhuma, passava aqui.

Agora o contrato exige tambem angleDeg0 por corpo e setMissionDay(day). Com
isso o verificador calcula onde a Terra e Marte estao mesmo (angulo0 +
movimento circular) em dias concretos, e confirma que window.__bench.getState
().shipAU fica fisicamente perto desses corpos nos momentos certos - partida
junto da Terra, chegada junto de Marte, e regresso junto da Terra. Uma pagina
que so declare os numeros certos sem os simular falha aqui.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "verify"))
from browser import has_bench, page_for  # noqa: E402

# (nome, raio em AU, periodo em dias)
EXPECTED = {
    "mercury": (0.387, 87.97),
    "venus": (0.723, 224.70),
    "earth": (1.000, 365.25),
    "mars": (1.524, 686.98),
}
MISSION = {
    "departurePhaseAngleDeg": (44.0, 6.0),    # graus, tolerancia absoluta
    "outboundDays": (259.0, 0.10),            # tolerancia relativa
    "stayDays": (455.0, 0.15),
    "returnDays": (259.0, 0.10),
    "totalDays": (970.0, 0.10),
}

# Tolerancia de encontro fisico, em UA. Generosa de proposito: nao estamos a
# certificar a precisao orbital da transferencia, so que a nave termina perto
# do corpo certo e nao apenas num ponto qualquer com os numeros certos por
# cima. 0.35 UA e ~23% do raio orbital de Marte.
RENDEZVOUS_TOL_AU = 0.35
LAUNCH_TOL_AU = 0.25

fails: list[str] = []


def body_pos_au(au_radius: float, angle_deg0: float, period_days: float, day: float) -> tuple[float, float]:
    theta = math.radians(angle_deg0 + 360.0 * day / period_days)
    return au_radius * math.cos(theta), au_radius * math.sin(theta)


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def rel(got: float, want: float) -> float:
    return abs(got - want) / want if want else float("inf")


def main() -> int:
    with page_for(frames_dir="_frames") as (page, errors):
        if not has_bench(page):
            print("FAIL: window.__bench nao existe (contrato do prompt nao cumprido)")
            return 1

        data = page.evaluate("() => ({bodies: window.__bench.bodies, mission: window.__bench.mission})")
        bodies = {str(b.get("name", "")).strip().lower(): b for b in (data.get("bodies") or [])}
        if not bodies:
            print("FAIL: window.__bench.bodies vazio ou ausente")
            return 1

        for name, (au, period) in EXPECTED.items():
            b = bodies.get(name)
            if b is None:
                fails.append(f"corpo em falta: {name}")
                continue
            got_au = float(b.get("auRadius", 0))
            got_p = float(b.get("periodDays", 0))
            if rel(got_au, au) > 0.05:
                fails.append(f"{name}: raio {got_au:.3f} AU, esperava {au} (+/-5%)")
            if rel(got_p, period) > 0.05:
                fails.append(f"{name}: periodo {got_p:.1f} d, esperava {period} (+/-5%)")
            if "angleDeg0" not in b:
                fails.append(f"{name}: angleDeg0 em falta (contrato exige-o para verificar o encontro com Marte)")

        # coerencia interna: a 3a lei de Kepler tem de bater certo entre corpos
        if "earth" in bodies and "mars" in bodies:
            try:
                e, m = bodies["earth"], bodies["mars"]
                ratio_p = float(m["periodDays"]) / float(e["periodDays"])
                ratio_a = (float(m["auRadius"]) / float(e["auRadius"])) ** 1.5
                if rel(ratio_p, ratio_a) > 0.08:
                    fails.append(
                        f"3a lei de Kepler violada entre Terra e Marte: "
                        f"T ratio {ratio_p:.3f} vs a^1.5 {ratio_a:.3f}"
                    )
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                fails.append("nao consegui verificar Kepler: campos em falta ou invalidos")

        # o angulo de partida declarado em mission tem de bater com angleDeg0
        # dos corpos - nao pode ser um numero decorado a parte da simulacao.
        if "earth" in bodies and "mars" in bodies and \
           "angleDeg0" in bodies["earth"] and "angleDeg0" in bodies["mars"]:
            try:
                phase = (float(bodies["mars"]["angleDeg0"]) - float(bodies["earth"]["angleDeg0"]) + 180) % 360 - 180
                want_phase = MISSION["departurePhaseAngleDeg"][0]
                if abs(abs(phase) - want_phase) > MISSION["departurePhaseAngleDeg"][1]:
                    fails.append(
                        f"angleDeg0 de Marte e Terra implicam fase de partida {phase:.1f} graus, "
                        f"nao bate com mission.departurePhaseAngleDeg (~{want_phase})"
                    )
            except (KeyError, TypeError, ValueError):
                fails.append("nao consegui cruzar angleDeg0 com mission.departurePhaseAngleDeg")

        mission = data.get("mission") or {}
        if not mission:
            fails.append("window.__bench.mission ausente")
        for key, (want, tol) in MISSION.items():
            if key not in mission:
                fails.append(f"mission.{key} em falta")
                continue
            got = float(mission[key])
            if key == "departurePhaseAngleDeg":
                if abs(got - want) > tol:
                    fails.append(f"mission.{key} = {got:.1f} graus, esperava {want} (+/-{tol})")
            elif rel(got, want) > tol:
                fails.append(f"mission.{key} = {got:.0f} d, esperava {want:.0f} (+/-{tol:.0%})")

        # o total tem de ser a soma das partes, nao um numero decorado
        try:
            parts = float(mission["outboundDays"]) + float(mission["stayDays"]) + float(mission["returnDays"])
            if rel(float(mission["totalDays"]), parts) > 0.03:
                fails.append(
                    f"totalDays {float(mission['totalDays']):.0f} nao bate com a soma das fases {parts:.0f}"
                )
        except (KeyError, TypeError, ValueError):
            pass

        # a nave tem de se mover
        s0 = page.evaluate("() => window.__bench.getState && window.__bench.getState()")
        page.wait_for_timeout(1500)
        s1 = page.evaluate("() => window.__bench.getState && window.__bench.getState()")
        if not s0 or not s1:
            fails.append("getState() ausente ou nao devolve nada")
        else:
            try:
                moved = abs(float(s1["shipAU"]["x"]) - float(s0["shipAU"]["x"])) + \
                        abs(float(s1["shipAU"]["y"]) - float(s0["shipAU"]["y"]))
                if moved < 1e-6 and float(s1["missionDay"]) == float(s0["missionDay"]):
                    fails.append("a animacao nao avanca: missionDay e posicao da nave estaticos")
            except (KeyError, TypeError, ValueError):
                fails.append("getState() nao respeita o formato {missionDay, shipAU:{x,y}}")

        # Encontro fisico: a nave tem mesmo de chegar perto da Terra/Marte
        # reais nos dias certos, nao so declarar os numeros da janela. Isto e
        # o que distingue "bonito" de "correto" - sem isto uma pagina que so
        # copia o contrato com valores estaticos passa (foi confirmado
        # empiricamente antes desta verificacao existir).
        has_seek = page.evaluate("() => typeof window.__bench.setMissionDay === 'function'")
        if not has_seek:
            fails.append("window.__bench.setMissionDay(day) em falta; nao consigo verificar o encontro com Marte")
        elif "earth" in bodies and "mars" in bodies and mission:
            try:
                earth, mars = bodies["earth"], bodies["mars"]
                e_au, e_period, e_a0 = float(earth["auRadius"]), float(earth["periodDays"]), float(earth["angleDeg0"])
                m_au, m_period, m_a0 = float(mars["auRadius"]), float(mars["periodDays"]), float(mars["angleDeg0"])
                out_d = float(mission["outboundDays"])
                stay_d = float(mission["stayDays"])

                checkpoints = [
                    (0.0, "partida", body_pos_au(e_au, e_a0, e_period, 0.0), LAUNCH_TOL_AU),
                    (out_d, "chegada a Marte", body_pos_au(m_au, m_a0, m_period, out_d), RENDEZVOUS_TOL_AU),
                    (out_d + stay_d, "fim da espera em Marte",
                     body_pos_au(m_au, m_a0, m_period, out_d + stay_d), RENDEZVOUS_TOL_AU),
                    (out_d + stay_d + float(mission["returnDays"]), "regresso a Terra",
                     body_pos_au(e_au, e_a0, e_period, out_d + stay_d + float(mission["returnDays"])),
                     RENDEZVOUS_TOL_AU),
                ]
                for day, label, expected, tol in checkpoints:
                    page.evaluate(f"() => window.__bench.setMissionDay({day})")
                    st = page.evaluate("() => window.__bench.getState()")
                    got = (float(st["shipAU"]["x"]), float(st["shipAU"]["y"]))
                    d = dist(got, expected)
                    if d > tol:
                        fails.append(
                            f"no dia {day:.0f} ({label}) a nave esta a {d:.2f} UA da posicao "
                            f"real esperada {expected[0]:.2f},{expected[1]:.2f} (tolerancia {tol} UA)"
                        )
            except (KeyError, TypeError, ValueError):
                fails.append("nao consegui verificar o encontro fisico com Marte: campos em falta ou invalidos")

        if errors:
            fails.append(f"{len(errors)} erros de JavaScript, ex: {errors[0][:120]}")

    if fails:
        print(f"FAIL ({len(fails)} problemas):")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS: orbitas, Kepler e janelas de lancamento/regresso verificadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
