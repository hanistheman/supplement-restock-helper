"""
Tests for the auth endpoints: register, login, and the get_current_user
dependency that protects every other route.
"""


def test_register_creates_user(client):
    res = client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter2pass"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    # Password must never be echoed back, hashed or otherwise.
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter2pass"})
    res = client.post("/auth/register", json={"email": "alice@example.com", "password": "differentpass"})
    assert res.status_code == 400


def test_register_short_password_rejected(client):
    res = client.post("/auth/register", json={"email": "alice@example.com", "password": "short"})
    assert res.status_code == 422


def test_register_invalid_email_rejected(client):
    res = client.post("/auth/register", json={"email": "not-an-email", "password": "hunter2pass"})
    assert res.status_code == 422


def test_login_succeeds_with_correct_credentials(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter2pass"})
    res = client.post("/auth/login", data={"username": "alice@example.com", "password": "hunter2pass"})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client):
    client.post("/auth/register", json={"email": "alice@example.com", "password": "hunter2pass"})
    res = client.post("/auth/login", data={"username": "alice@example.com", "password": "wrongpassword"})
    assert res.status_code == 401


def test_login_fails_for_unknown_email(client):
    res = client.post("/auth/login", data={"username": "ghost@example.com", "password": "whatever123"})
    assert res.status_code == 401


def test_me_requires_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    headers = auth_headers("bob@example.com", "bobspassword")
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "bob@example.com"


def test_invalid_token_rejected(client):
    res = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_login_returns_both_tokens(client, auth_tokens):
    tokens = auth_tokens()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


class TestRefreshFlow:
    def test_refresh_issues_new_access_token(self, client, auth_tokens):
        tokens = auth_tokens()
        res = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert res.status_code == 200
        new_tokens = res.json()
        assert "access_token" in new_tokens
        # New access token should actually work against a protected route.
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
        assert me.status_code == 200

    def test_refresh_token_is_rotated(self, client, auth_tokens):
        """Using a refresh token once should invalidate it — it can't be reused."""
        tokens = auth_tokens()
        first_refresh = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert first_refresh.status_code == 200

        # Reusing the SAME original refresh token a second time should fail.
        second_attempt = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert second_attempt.status_code == 401

    def test_new_refresh_token_from_rotation_works(self, client, auth_tokens):
        tokens = auth_tokens()
        first = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
        # The NEW refresh token issued by rotation should itself be usable.
        second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert second.status_code == 200

    def test_invalid_refresh_token_rejected(self, client):
        res = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
        assert res.status_code == 401

    def test_revoked_refresh_token_rejected_after_logout(self, client, auth_tokens):
        tokens = auth_tokens()
        logout_res = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
        assert logout_res.status_code == 204

        refresh_res = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refresh_res.status_code == 401

    def test_logout_with_already_invalid_token_does_not_error(self, client):
        # Logging out with a bogus/already-used token should be a harmless
        # no-op, not a 500 — the client's job (clearing local state) still
        # happens regardless of whether the server had anything to revoke.
        res = client.post("/auth/logout", json={"refresh_token": "garbage-token"})
        assert res.status_code == 204
