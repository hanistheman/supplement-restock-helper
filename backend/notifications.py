"""
Low-stock notification logic. Kept separate from main.py so it can be
triggered from a route, a script, or a test without duplicating the
selection/formatting logic.
"""
import logging

from sqlalchemy.orm import Session

import models
import logic
from email_service import send_email

logger = logging.getLogger(__name__)

# Statuses worth emailing a user about — "ok" is deliberately excluded.
NOTIFY_STATUSES = {"low", "critical", "overdue"}


def get_low_stock_supplements(user: models.User) -> list[dict]:
    """Returns the subset of a user's supplements currently at a notify-worthy status."""
    results = []
    for s in user.supplements:
        days_left = logic.days_remaining(s.start_date, s.total_doses, _doses_per_day(s))
        status = logic.status_for(days_left)
        if status in NOTIFY_STATUSES:
            results.append({"name": s.name, "days_remaining": days_left, "status": status})
    return results


def _doses_per_day(s: models.Supplement) -> float:
    return logic.doses_per_day_from_frequency(s.dose_amount, s.frequency_count, s.frequency_unit)


def build_email_body(low_stock: list[dict]) -> str:
    lines = ["Here's what's running low:\n"]
    # Most urgent first — overdue items should be the first thing the user reads.
    for item in sorted(low_stock, key=lambda i: i["days_remaining"]):
        if item["days_remaining"] < 0:
            timing = f"{abs(item['days_remaining'])} days overdue"
        else:
            timing = f"{item['days_remaining']} days left"
        lines.append(f"- {item['name']} ({timing})")
    lines.append("\n— Supplement Restock Tracker")
    return "\n".join(lines)


def run_low_stock_check(db: Session) -> int:
    """
    Checks every opted-in user's supplements and emails anyone with at
    least one item at low/critical/overdue status. Returns the number of
    emails sent, so callers (routes, scripts, tests) can report a result.
    """
    users = db.query(models.User).filter(models.User.notifications_enabled.is_(True)).all()
    sent = 0
    for user in users:
        low_stock = get_low_stock_supplements(user)
        if not low_stock:
            continue
        subject = f"Supplement Tracker: {len(low_stock)} item(s) need restocking"
        try:
            send_email(user.email, subject, build_email_body(low_stock))
        except Exception:
            # One undeliverable mailbox or a transient SMTP outage shouldn't
            # abort the whole batch — log it and keep going so every other
            # opted-in user still gets their notification.
            logger.exception("Failed to send low-stock email to %s", user.email)
            continue
        sent += 1
    return sent