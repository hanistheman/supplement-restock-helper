import logging

from django.conf import settings
from django.core.mail import send_mail

from logic import DAYS_PER_UNIT, days_remaining, doses_per_day_from_frequency, status_for
from .models import User

logger = logging.getLogger(__name__)
NOTIFY_STATUSES = {"low", "critical", "overdue"}


def get_low_stock_supplements(user):
    items = []
    for item in user.supplements.all():
        per_day = doses_per_day_from_frequency(item.dose_amount, item.frequency_count, item.frequency_unit)
        skipped = item.skipped_days.filter(date__gte=item.start_date).count()
        adjustment = round(skipped * DAYS_PER_UNIT[item.frequency_unit] / item.frequency_count)
        remaining = days_remaining(item.start_date, item.total_doses, per_day) + adjustment
        state = status_for(remaining)
        if state in NOTIFY_STATUSES:
            items.append({"name": item.name, "days_remaining": remaining, "status": state})
    return items


def build_email_body(items):
    lines = ["Here's what's running low:\n"]
    for item in sorted(items, key=lambda row: row["days_remaining"]):
        days = item["days_remaining"]
        timing = f"{abs(days)} days overdue" if days < 0 else f"{days} days left"
        lines.append(f"- {item['name']} ({timing})")
    lines.append("\n— Supplement Restock Tracker")
    return "\n".join(lines)


def run_low_stock_check():
    sent = 0
    users = User.objects.filter(notifications_enabled=True).prefetch_related("supplements")
    for user in users:
        items = get_low_stock_supplements(user)
        if not items:
            continue
        subject = f"Supplement Tracker: {len(items)} item(s) need restocking"
        try:
            if settings.EMAIL_HOST:
                send_mail(subject, build_email_body(items), settings.DEFAULT_FROM_EMAIL, [user.email])
            else:
                print(f"[email:console-fallback] To: {user.email} | Subject: {subject}\n{build_email_body(items)}\n")
        except Exception:
            logger.exception("Failed to send low-stock email to %s", user.email)
            continue
        sent += 1
    return sent
