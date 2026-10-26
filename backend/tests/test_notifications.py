from datetime import date
from unittest.mock import patch

from django.test import override_settings
import pytest

from tracker.models import Supplement, User
from tracker.services import build_email_body, get_low_stock_supplements, run_low_stock_check

pytestmark = pytest.mark.django_db


def add_supplement(user, name, doses, start_date=None):
    return Supplement.objects.create(user=user, name=name, start_date=start_date or date.today(), total_doses=doses)


def test_ok_supplements_are_excluded():
    user = User.objects.create(email="ok@example.com", hashed_password="unused")
    add_supplement(user, "Plenty Left", 30)
    assert get_low_stock_supplements(user) == []


def test_low_and_critical_supplements_are_included():
    user = User.objects.create(email="low@example.com", hashed_password="unused")
    add_supplement(user, "Running Low", 5)
    add_supplement(user, "Almost Out", 2)
    add_supplement(user, "Plenty Left", 30)
    items = get_low_stock_supplements(user)
    assert {item["name"] for item in items} == {"Running Low", "Almost Out"}


def test_email_body_orders_urgent_items_and_describes_overdue():
    content = build_email_body([
        {"name": "Later", "days_remaining": 5},
        {"name": "Overdue", "days_remaining": -3},
    ])
    assert content.index("Overdue") < content.index("Later")
    assert "3 days overdue" in content


@override_settings(EMAIL_HOST="smtp.example.test")
def test_batch_emails_only_opted_in_users_with_low_stock():
    urgent = User.objects.create(email="notify@example.com", hashed_password="x")
    opted_out = User.objects.create(email="optout@example.com", hashed_password="x", notifications_enabled=False)
    fine = User.objects.create(email="fine@example.com", hashed_password="x")
    add_supplement(urgent, "Almost Out", 1)
    add_supplement(opted_out, "Also Almost Out", 1)
    add_supplement(fine, "Plenty Left", 60)
    with patch("tracker.services.send_mail") as send:
        assert run_low_stock_check() == 1
    send.assert_called_once()
    assert send.call_args.args[3] == ["notify@example.com"]


@override_settings(EMAIL_HOST="smtp.example.test")
def test_email_failure_does_not_stop_batch():
    first = User.objects.create(email="bounces@example.com", hashed_password="x")
    second = User.objects.create(email="delivered@example.com", hashed_password="x")
    add_supplement(first, "First", 1)
    add_supplement(second, "Second", 1)
    with patch("tracker.services.send_mail", side_effect=[RuntimeError("mail unavailable"), 1]) as send:
        assert run_low_stock_check() == 1
    assert send.call_count == 2


def test_notification_endpoint_requires_shared_secret(client, settings):
    settings.NOTIFICATIONS_SECRET = "test-secret"
    assert client.post("/notifications/run").status_code == 401
    assert client.post("/notifications/run", headers={"X-Notifications-Secret": "wrong"}).status_code == 401
    accepted = client.post("/notifications/run", headers={"X-Notifications-Secret": "test-secret"})
    assert accepted.status_code == 200
    assert accepted.json() == {"emails_sent": 0}


def test_notification_preference_requires_auth_and_can_be_changed(client, auth_headers):
    assert client.patch("/auth/me/notifications", json={"notifications_enabled": False}).status_code == 401
    headers = auth_headers()
    changed = client.patch("/auth/me/notifications", headers=headers, json={"notifications_enabled": False})
    assert changed.status_code == 200
    assert changed.json()["notifications_enabled"] is False
    assert client.get("/auth/me", headers=headers).json()["notifications_enabled"] is False
