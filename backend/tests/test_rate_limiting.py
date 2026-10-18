"""
Tests that auth endpoints are rate-limited, protecting against
brute-force login/registration attempts.
"""


def test_login_rate_limited_after_five_attempts(client):
    for _ in range(5):
        res = client.post("/auth/login", data={"username": "nobody@example.com", "password": "wrong"})
        assert res.status_code == 401  # under the limit, just wrong credentials

    res = client.post("/auth/login", data={"username": "nobody@example.com", "password": "wrong"})
    assert res.status_code == 429


def test_register_rate_limited_after_five_attempts(client):
    for i in range(5):
        res = client.post(
            "/auth/register", json={"email": f"user{i}@example.com", "password": "testpassword123"}
        )
        assert res.status_code == 201

    res = client.post(
        "/auth/register", json={"email": "oneemailover@example.com", "password": "testpassword123"}
    )
    assert res.status_code == 429
