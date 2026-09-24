#!/usr/bin/env python3
"""Regista consumo, RAM e temperatura durante as runs. Stdlib apenas.

    python3 monitor.py --out power.csv &
    ./bench.sh
    kill %1

Fontes de potencia, por esta ordem, e a coluna watts_source diz qual foi usada:

  rapl        /sys/class/powercap/intel-rapl:N/energy_uj (so os dominios de
              topo: o intel-rapl:N:M e um subdominio ja contido no pai, e
              soma-los contava o mesmo consumo duas vezes). No Ubuntu o
              energy_uj so e legivel como root, por isso num utilizador normal
              esta fonte nao existe.
  amdgpu_ppt  hwmon "amdgpu", power1_average (label PPT, Package Power
              Tracking). Legivel sem root. E a potencia do SoC (CPU + GPU do
              Ryzen AI MAX), NAO a da tomada: fica de fora RAM, SSD, ventoinhas
              e as perdas da fonte. Num slide diz "potencia do SoC", nunca
              "consumo da maquina".

Sem nenhuma das duas, watts fica vazio em vez de inventar um numero - mede com
um wattimetro de tomada e regista a mao. Um numero de energia que nao sabes de
onde veio nao vale nada num slide.

Ate 2026-09-24 este script so tentava o RAPL, e todas as linhas de todos os
power*.csv anteriores tem watts vazio (ver RESULTS.md 6.3).
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
import sys
import time
from pathlib import Path


def rapl_paths() -> list[str]:
    # So intel-rapl:N, nunca intel-rapl:N:M (subdominio contido no pai).
    return sorted(p for p in glob.glob("/sys/class/powercap/intel-rapl:*/energy_uj")
                  if re.fullmatch(r"intel-rapl:\d+", Path(p).parent.name))


def read_uj(paths) -> int | None:
    total = 0
    ok = False
    for p in paths:
        try:
            total += int(Path(p).read_text().strip())
            ok = True
        except (OSError, ValueError):
            continue
    return total if ok else None


def hwmon_by_name(name: str) -> Path | None:
    for h in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            if Path(h, "name").read_text().strip() == name:
                return Path(h)
        except OSError:
            continue
    return None


def read_num(p: Path | None) -> float | None:
    if p is None:
        return None
    try:
        return float(p.read_text().strip())
    except (OSError, ValueError):
        return None


def mem_used_gib() -> float | None:
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            info[k] = int(v.strip().split()[0])
        return (info["MemTotal"] - info["MemAvailable"]) / 1024 / 1024
    except (OSError, KeyError, ValueError):
        return None


def cpu_temp_c(k10: Path | None) -> float | None:
    # k10temp Tctl e a temperatura de controlo do Ryzen. As thermal_zone desta
    # maquina so tem a acpitz, que marca 0 - era por isso que a coluna saia vazia.
    t = read_num(k10 / "temp1_input") if k10 else None
    if t is not None and 20 < t / 1000 < 120:
        return round(t / 1000, 1)
    best = None
    for p in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        v = read_num(Path(p))
        if v is not None and 20 < v / 1000 < 120:
            best = v / 1000 if best is None else max(best, v / 1000)
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="power.csv")
    ap.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args()

    paths = rapl_paths()
    prev_uj = read_uj(paths)
    amdgpu = hwmon_by_name("amdgpu")
    ppt = amdgpu / "power1_average" if amdgpu else None
    k10 = hwmon_by_name("k10temp")

    if prev_uj is not None:
        source = "rapl"
    elif read_num(ppt) is not None:
        source = "amdgpu_ppt"
    else:
        source = ""
    print({"rapl": "potencia: RAPL (dominios de topo)",
           "amdgpu_ppt": "potencia: amdgpu PPT (SoC, nao a tomada) - RAPL ilegivel sem root",
           "": "AVISO: sem RAPL legivel nem amdgpu PPT. watts fica vazio; mede com wattimetro."}[source],
          file=sys.stderr)

    prev_t = time.time()
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "watts", "mem_used_gib", "cpu_temp_c", "watts_source"])
        fh.flush()
        try:
            while True:
                time.sleep(args.interval)
                now = time.time()
                watts = ""
                if source == "rapl":
                    uj = read_uj(paths)
                    if uj is not None and prev_uj is not None and now > prev_t:
                        delta = uj - prev_uj
                        if delta >= 0:  # ignora wrap do contador
                            watts = round(delta / 1e6 / (now - prev_t), 2)
                    prev_uj = uj
                elif source == "amdgpu_ppt":
                    uw = read_num(ppt)
                    if uw is not None:
                        watts = round(uw / 1e6, 2)
                prev_t = now
                mem = mem_used_gib()
                temp = cpu_temp_c(k10)
                w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), watts,
                            "" if mem is None else round(mem, 2),
                            "" if temp is None else temp, source])
                fh.flush()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
