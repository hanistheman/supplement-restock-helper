"""
Unit tests for logic.py — pure functions, no DB or network involved, so
these run instantly and don't need Postgres, Docker, or the API running.

Run with: pytest tests/test_logic.py -v
"""
from datetime import date

import pytest

from logic import days_remaining, restock_date, status_for, doses_per_day_from_frequency


class TestDosesPerDayFromFrequency:
    def test_once_daily_is_unchanged(self):
        # 1 dose, once per day -> 1 dose/day (matches old plain doses_per_day behavior).
        assert doses_per_day_from_frequency(1, 1, "day") == 1

    def test_multiple_doses_daily(self):
        assert doses_per_day_from_frequency(2, 3, "day") == 6

    def test_once_weekly(self):
        assert doses_per_day_from_frequency(1, 1, "week") == pytest.approx(1 / 7)

    def test_multiple_times_per_week(self):
        # 2 doses, 3 times a week -> 6 doses / 7 days.
        assert doses_per_day_from_frequency(2, 3, "week") == pytest.approx(6 / 7)

    def test_once_monthly(self):
        assert doses_per_day_from_frequency(1, 1, "month") == pytest.approx(1 / 30.44)

    def test_once_yearly(self):
        assert doses_per_day_from_frequency(1, 1, "year") == pytest.approx(1 / 365.25)

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError):
            doses_per_day_from_frequency(1, 1, "fortnight")

    def test_zero_dose_amount_raises(self):
        with pytest.raises(ValueError):
            doses_per_day_from_frequency(0, 1, "day")

    def test_zero_frequency_count_raises(self):
        with pytest.raises(ValueError):
            doses_per_day_from_frequency(1, 0, "day")

    def test_feeds_correctly_into_days_remaining(self):
        # 2 capsules, once a week -> ~0.2857 doses/day. A 30-dose bottle
        # should last roughly 105 days (30 / (2/7)).
        rate = doses_per_day_from_frequency(2, 1, "week")
        result = days_remaining(date(2026, 1, 1), 30, rate, today=date(2026, 1, 1))
        assert result == 105


class TestDaysRemaining:
    def test_no_time_elapsed(self):
        # Just started a 90-day bottle today — all 90 days should remain.
        assert days_remaining(date(2026, 1, 1), 90, 1, today=date(2026, 1, 1)) == 90

    def test_partway_through(self):
        # 90-dose bottle, 1/day, 30 days elapsed -> 60 left.
        assert days_remaining(date(2026, 1, 1), 90, 1, today=date(2026, 1, 31)) == 60

    def test_exactly_out(self):
        assert days_remaining(date(2026, 1, 1), 30, 1, today=date(2026, 1, 31)) == 0

    def test_overdue_is_negative(self):
        # 10 days past when a 30-dose bottle should have run out.
        assert days_remaining(date(2026, 1, 1), 30, 1, today=date(2026, 2, 10)) == -10

    def test_fractional_doses_per_day(self):
        # 30 doses at 0.5/day = 60 days of supply; 10 elapsed -> 50 left.
        assert days_remaining(date(2026, 1, 1), 30, 0.5, today=date(2026, 1, 11)) == 50

    def test_multiple_doses_per_day(self):
        # 60 doses at 2/day = 30 days of supply; 5 elapsed -> 25 left.
        assert days_remaining(date(2026, 1, 1), 60, 2, today=date(2026, 1, 6)) == 25

    def test_defaults_to_today_when_not_provided(self):
        # Started today, none elapsed yet -> exactly total_doses / doses_per_day.
        assert days_remaining(date.today(), 10, 1) == 10

    def test_zero_doses_per_day_raises(self):
        with pytest.raises(ValueError):
            days_remaining(date(2026, 1, 1), 30, 0, today=date(2026, 1, 1))

    def test_negative_doses_per_day_raises(self):
        with pytest.raises(ValueError):
            days_remaining(date(2026, 1, 1), 30, -1, today=date(2026, 1, 1))


class TestRestockDate:
    def test_simple_case(self):
        assert restock_date(date(2026, 1, 1), 30, 1) == date(2026, 1, 31)

    def test_fractional_doses_per_day(self):
        # 30 doses at 0.5/day = 60 days of supply.
        assert restock_date(date(2026, 1, 1), 30, 0.5) == date(2026, 3, 2)

    def test_rounds_to_nearest_day(self):
        # 10 doses at 3/day = 3.33... days -> rounds to 3.
        assert restock_date(date(2026, 1, 1), 10, 3) == date(2026, 1, 4)


class TestStatusFor:
    def test_ok_when_more_than_a_week_left(self):
        assert status_for(8) == "ok"
        assert status_for(30) == "ok"

    def test_low_boundary(self):
        # 4-7 days is "low"
        assert status_for(7) == "low"
        assert status_for(4) == "low"

    def test_critical_boundary(self):
        # 0-3 days is "critical"
        assert status_for(3) == "critical"
        assert status_for(0) == "critical"

    def test_overdue_when_negative(self):
        assert status_for(-1) == "overdue"
        assert status_for(-100) == "overdue"
