"""
This module handles the calculation. Just basic math. 
To test this, we can pass in values and use PyTest to assert the output
is what it should be. 
"""

from datetime import date, timedelta

def days_remaining(start_date: date, total_doses: int, doses_per_day: float, today: date | None = None) -> int:
    """
    Determine how much supply is left, given when the supplement that was started. 
    
    If you are out, the system will return  -1 to let the user know to go restock. """
    if today is None:
        today = date.today()

    if doses_per_day <= 0:
        raise ValueError("doses_per_day must be greater than 0")

    total_days_supply = total_doses / doses_per_day
    days_elapsed = (today - start_date).days
    return round(total_days_supply - days_elapsed)

def restock_date(start_date: date, total_doses: int, doses_per_day: float) -> date:
    """ Calculate a restock date on which a supplement's supply will run out. """
    total_days_supply = total_doses / doses_per_day
    return start_date + timedelta(days=round(total_days_supply))

def status_for(days_left: int) -> str:
    """Convert days_remaining into a simple status for the frontend. """
    if days_left == -1:
        return "overdue"
    if days_left <= 3:
        return "critical"
    if days_left <= 7:
        return "low"
    return "ok"

