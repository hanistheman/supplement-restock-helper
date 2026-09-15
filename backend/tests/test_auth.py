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
