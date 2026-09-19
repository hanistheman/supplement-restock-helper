"""
Tests for the notification system: who gets selected for a low-stock
email, what the email says, and that the trigger endpoint is properly
secured against unauthorized calls.
"""
from datetime import date, timedelta
from unittest.mock import patch

import models
from notifications import get_low_stock_supplements, build_email_body, run_low_stock_check


def _make_supplement(db_session, user, name, days_remaining_target, frequency_unit="day"):
    """Creates a supplement whose days_remaining works out to roughly the target."""
    start_date = date.today() - timedelta(days=0)
    total_doses = max(days_remaining_target, 1)
    supplement = models.Supplement(
        user_id=user.id,
        name=name,
        start_date=start_date,
        total_doses=total_doses,
        dose_amount=1,
        frequency_count=1,
        frequency_unit=frequency_unit,
    )
    db_session.add(supplement)
    db_session.commit()
    db_session.refresh(supplement)
    return supplement


class TestGetLowStockSupplements:
    def test_ok_status_excluded(self, db_session):
        user = models.User(email="a@example.com", hashed_password="x")
        db_session.add(user)
        db_session.commit()
        _make_supplement(db_session, user, "Plenty Left", 30)  # status "ok"

        db_session.refresh(user)
        assert get_low_stock_supplements(user) == []

    def test_low_and_critical_included(self, db_session):
        user = models.User(email="b@example.com", hashed_password="x")
        db_session.add(user)
        db_session.commit()
        _make_supplement(db_session, user, "Running Low", 5)     # "low"
        _make_supplement(db_session, user, "Almost Out", 2)      # "critical"
        _make_supplement(db_session, user, "Plenty Left", 30)    # "ok" — excluded

        db_session.refresh(user)
        results = get_low_stock_supplements(user)
        names = {r["name"] for r in results}
        assert names == {"Running Low", "Almost Out"}


class TestBuildEmailBody:
    def test_sorts_most_urgent_first(self):
        low_stock = [
            {"name": "B", "days_remaining": 5, "status": "low"},
            {"name": "A", "days_remaining": -2, "status": "overdue"},
        ]
        body = build_email_body(low_stock)
        assert body.index("A") < body.index("B")

    def test_overdue_wording(self):
        body = build_email_body([{"name": "X", "days_remaining": -3, "status": "overdue"}])
        assert "3 days overdue" in body


class TestRunLowStockCheck:
    def test_sends_only_to_opted_in_users_with_low_stock(self, db_session):
        opted_in_with_low_stock = models.User(email="notify-me@example.com", hashed_password="x", notifications_enabled=True)
        opted_out = models.User(email="leave-me-alone@example.com", hashed_password="x", notifications_enabled=False)
        opted_in_but_fine = models.User(email="all-good@example.com", hashed_password="x", notifications_enabled=True)
        db_session.add_all([opted_in_with_low_stock, opted_out, opted_in_but_fine])
        db_session.commit()

        _make_supplement(db_session, opted_in_with_low_stock, "Almost Out", 1)
        _make_supplement(db_session, opted_out, "Also Almost Out", 1)
        _make_supplement(db_session, opted_in_but_fine, "Plenty Left", 60)

        with patch("notifications.send_email") as mock_send:
            sent_count = run_low_stock_check(db_session)

        assert sent_count == 1
        mock_send.assert_called_once()
        called_to_email = mock_send.call_args[0][0]
        assert called_to_email == "notify-me@example.com"


class TestNotificationsEndpoint:
    def test_requires_secret_header(self, client):
        res = client.post("/notifications/run")
        assert res.status_code == 401

    def test_rejects_wrong_secret(self, client):
        res = client.post("/notifications/run", headers={"X-Notifications-Secret": "wrong"})
        assert res.status_code == 401

    def test_accepts_correct_secret(self, client, monkeypatch):
        monkeypatch.setenv("NOTIFICATIONS_SECRET", "test-secret-123")
        res = client.post("/notifications/run", headers={"X-Notifications-Secret": "test-secret-123"})
        assert res.status_code == 200
        assert "emails_sent" in res.json()


class TestNotificationSettingsEndpoint:
    def test_toggle_requires_auth(self, client):
        res = client.patch("/auth/me/notifications", json={"notifications_enabled": False})
        assert res.status_code == 401

    def test_toggle_updates_setting(self, client, auth_headers):
        headers = auth_headers()
        res = client.patch("/auth/me/notifications", headers=headers, json={"notifications_enabled": False})
        assert res.status_code == 200
        assert res.json()["notifications_enabled"] is False

        check = client.get("/auth/me", headers=headers)
        assert check.json()["notifications_enabled"] is False