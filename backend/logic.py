"""
Pure calculation logic — no DB, no FastAPI. This makes it trivial to unit
test: you just pass in values and check the output.
"""
from datetime import date, timedelta

# Average day-count used to convert "per month" / "per year" into a daily
# rate. Calendar months/years vary in length, so this is an approximation —
# fine for a restock estimate, not something that needs to be exact to the
# day. Weeks are exact (always 7 days), so no approximation there.
DAYS_PER_UNIT = {
    "day": 1,
    "week": 7,
    "month": 30.44,   # 365.25 / 12
    "year": 365.25,
}


def doses_per_day_from_frequency(dose_amount: float, frequency_count: float, frequency_unit: str) -> float:
    """
    Converts a human-entered frequency (e.g. "2 doses every 1 week") into
    the doses-per-day rate that days_remaining()/restock_date() expect.

    dose_amount: how many doses are taken each time (e.g. 2 capsules)
    frequency_count: how many times per frequency_unit (e.g. 3 times per week)
    frequency_unit: "day" | "week" | "month" | "year"
    """
    if frequency_unit not in DAYS_PER_UNIT:
        raise ValueError(f"Unknown frequency_unit: {frequency_unit!r}")
    if dose_amount <= 0 or frequency_count <= 0:
        raise ValueError("dose_amount and frequency_count must be greater than 0")

    days_per_unit = DAYS_PER_UNIT[frequency_unit]
    return (dose_amount * frequency_count) / days_per_unit


def days_remaining(start_date: date, total_doses: int, doses_per_day: float, today: date | None = None) -> int:
    """
    How many days of supply are left, given when the bottle was started.
    Returns a value that can go negative if you're overdue to restock.
    """
    if today is None:
        today = date.today()

    if doses_per_day <= 0:
        raise ValueError("doses_per_day must be greater than 0")

    total_days_supply = total_doses / doses_per_day
    days_elapsed = (today - start_date).days
    return round(total_days_supply - days_elapsed)


def restock_date(start_date: date, total_doses: int, doses_per_day: float) -> date:
    """The calendar date on which the supply runs out."""
    total_days_supply = total_doses / doses_per_day
    return start_date + timedelta(days=round(total_days_supply))


def status_for(days_left: int) -> str:
    """Bucket days_remaining into a simple status the frontend can color-code."""
    if days_left < 0:
        return "overdue"
    if days_left <= 3:
        return "critical"
    if days_left <= 7:
        return "low"
    return "ok"

