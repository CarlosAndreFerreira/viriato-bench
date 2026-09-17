#!/usr/bin/env python3
"""Regista consumo, RAM e temperatura durante as runs. Stdlib apenas.

    python3 monitor.py --out power.csv &
    ./bench.sh
    kill %1

No Ryzen AI MAX+ 395 le o RAPL em /sys/class/powercap/. Se o kernel nao expuser
o RAPL (acontece em varios AMD), a coluna watts fica vazia em vez de inventar um
numero - nesse caso mede com um wattimetro de tomada e regista a mao. Um numero
de energia que nao sabes de onde veio nao vale nada num slide.
"""
from __future__ import annotations

import argparse
import csv
import glob
import time
from pathlib import Path

RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"


def rapl_paths() -> list[str]:
    out = [p for p in glob.glob("/sys/class/powercap/*/energy_uj")]
    return out or ([RAPL] if Path(RAPL).exists() else [])


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


def mem_used_gib() -> float | None:
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            info[k] = int(v.strip().split()[0])
        return (info["MemTotal"] - info["MemAvailable"]) / 1024 / 1024
    except (OSError, KeyError, ValueError):
        return None


def cpu_temp_c() -> float | None:
    best = None
    for p in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            t = int(Path(p).read_text().strip()) / 1000
        except (OSError, ValueError):
            continue
        if 20 < t < 120:
            best = t if best is None else max(best, t)
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="power.csv")
    ap.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args()

    paths = rapl_paths()
    if not paths:
        print("AVISO: RAPL indisponivel. watts fica vazio; mede com wattimetro.")

    prev_uj, prev_t = read_uj(paths), time.time()
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "watts", "mem_used_gib", "cpu_temp_c"])
        fh.flush()
        try:
            while True:
                time.sleep(args.interval)
                now, uj = time.time(), read_uj(paths)
                watts = ""
                if uj is not None and prev_uj is not None and now > prev_t:
                    delta = uj - prev_uj
                    if delta >= 0:  # ignora wrap do contador
                        watts = round(delta / 1e6 / (now - prev_t), 2)
                prev_uj, prev_t = uj, now
                w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), watts,
                            round(mem_used_gib() or 0, 2) or "", cpu_temp_c() or ""])
                fh.flush()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
