"""Agendamento de tarefas recorrentes.

Usado pelo Viriato's Maze para agendar torneios mensais e semanais.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Recurrence:
    start: date
    kind: str          # "daily" | "weekly" | "monthly"
    interval: int = 1


def add_months(d: date, months: int) -> date:
    """Avanca `months` meses, mantendo o dia do mes sempre que possivel.

    Quando o mes de destino nao tem esse dia (ex: 31 de janeiro + 1 mes),
    o resultado deve ser o ultimo dia do mes de destino.
    """
    total = (d.year * 12 + (d.month - 1)) + months
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, d.day)


def occurrences(rec: Recurrence, count: int) -> list[date]:
    """Devolve as primeiras `count` ocorrencias, incluindo a data de inicio."""
    if count <= 0:
        return []
    if rec.interval < 1:
        raise ValueError("interval tem de ser >= 1")

    out = [rec.start]
    while len(out) < count:
        last = out[-1]
        if rec.kind == "daily":
            out.append(last + timedelta(days=rec.interval))
        elif rec.kind == "weekly":
            out.append(last + timedelta(weeks=rec.interval))
        elif rec.kind == "monthly":
            out.append(add_months(last, rec.interval))
        else:
            raise ValueError(f"kind desconhecido: {rec.kind}")
    return out


def business_days_between(a: date, b: date) -> int:
    """Numero de dias uteis (seg-sex) no intervalo [a, b), a < b."""
    if b <= a:
        return 0
    days = 0
    cur = a
    while cur < b:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)
    return days


if __name__ == "__main__":
    r = Recurrence(date(2026, 1, 31), "monthly")
    for d in occurrences(r, 5):
        print(d, calendar.day_abbr[d.weekday()])
