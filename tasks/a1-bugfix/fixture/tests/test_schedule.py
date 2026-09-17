from datetime import date

import pytest

from schedule import Recurrence, add_months, business_days_between, occurrences


def test_add_months_simple():
    assert add_months(date(2026, 1, 15), 1) == date(2026, 2, 15)
    assert add_months(date(2026, 11, 3), 2) == date(2027, 1, 3)


def test_add_months_clamps_to_last_day():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert add_months(date(2026, 3, 31), 1) == date(2026, 4, 30)


def test_add_months_backwards():
    assert add_months(date(2026, 3, 31), -1) == date(2026, 2, 28)
    assert add_months(date(2026, 1, 10), -1) == date(2025, 12, 10)


def test_monthly_occurrences_do_not_drift():
    rec = Recurrence(date(2026, 1, 31), "monthly")
    got = occurrences(rec, 4)
    assert got == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
        date(2026, 4, 30),
    ]


def test_daily_and_weekly():
    assert occurrences(Recurrence(date(2026, 5, 1), "daily", 3), 3) == [
        date(2026, 5, 1),
        date(2026, 5, 4),
        date(2026, 5, 7),
    ]
    assert occurrences(Recurrence(date(2026, 5, 1), "weekly"), 2) == [
        date(2026, 5, 1),
        date(2026, 5, 8),
    ]


def test_occurrences_edges():
    assert occurrences(Recurrence(date(2026, 5, 1), "daily"), 0) == []
    with pytest.raises(ValueError):
        occurrences(Recurrence(date(2026, 5, 1), "daily", 0), 3)
    with pytest.raises(ValueError):
        occurrences(Recurrence(date(2026, 5, 1), "yearly"), 3)


def test_business_days():
    assert business_days_between(date(2026, 5, 4), date(2026, 5, 11)) == 5
    assert business_days_between(date(2026, 5, 11), date(2026, 5, 4)) == 0
