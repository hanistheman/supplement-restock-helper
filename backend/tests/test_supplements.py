"""
Tests that supplement/source endpoints are properly scoped per user.

These are arguably the most important tests in the project: a regression
here means one user's private data leaking to another user, which is a
real security bug, not just a broken feature.
"""


def _create_supplement(client, headers, name="Vitamin D3"):
    res = client.post(
        "/supplements",
        headers=headers,
        json={
            "name": name,
            "start_date": "2026-01-01",
            "total_doses": 90,
            "dose_amount": 1,
            "frequency_count": 1,
            "frequency_unit": "day",
        },
    )
    assert res.status_code == 201
    return res.json()


def test_list_requires_auth(client):
    res = client.get("/supplements")
    assert res.status_code == 401


def test_create_and_list_own_supplement(client, auth_headers):
    headers = auth_headers()
    _create_supplement(client, headers)
    res = client.get("/supplements", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["name"] == "Vitamin D3"


def test_users_do_not_see_each_others_supplements(client, auth_headers):
    alice_headers = auth_headers("alice@example.com", "alicepassword")
    bob_headers = auth_headers("bob@example.com", "bobpassword")

    _create_supplement(client, alice_headers, name="Alice's Vitamin D3")

    alice_list = client.get("/supplements", headers=alice_headers).json()
    bob_list = client.get("/supplements", headers=bob_headers).json()

    assert len(alice_list) == 1
    assert len(bob_list) == 0


def test_user_cannot_get_another_users_supplement_by_id(client, auth_headers):
    alice_headers = auth_headers("alice@example.com", "alicepassword")
    bob_headers = auth_headers("bob@example.com", "bobpassword")

    alice_supplement = _create_supplement(client, alice_headers)

    res = client.get(f"/supplements/{alice_supplement['id']}", headers=bob_headers)
    # 404, not 403 — Bob shouldn't be able to distinguish "exists but isn't
    # mine" from "doesn't exist" for another user's data.
    assert res.status_code == 404


def test_user_cannot_update_another_users_supplement(client, auth_headers):
    alice_headers = auth_headers("alice@example.com", "alicepassword")
    bob_headers = auth_headers("bob@example.com", "bobpassword")

    alice_supplement = _create_supplement(client, alice_headers)

    res = client.put(
        f"/supplements/{alice_supplement['id']}",
        headers=bob_headers,
        json={"name": "Hijacked"},
    )
    assert res.status_code == 404

    # Confirm it's genuinely untouched.
    check = client.get(f"/supplements/{alice_supplement['id']}", headers=alice_headers)
    assert check.json()["name"] == "Vitamin D3"


def test_user_cannot_delete_another_users_supplement(client, auth_headers):
    alice_headers = auth_headers("alice@example.com", "alicepassword")
    bob_headers = auth_headers("bob@example.com", "bobpassword")

    alice_supplement = _create_supplement(client, alice_headers)

    res = client.delete(f"/supplements/{alice_supplement['id']}", headers=bob_headers)
    assert res.status_code == 404

    still_there = client.get(f"/supplements/{alice_supplement['id']}", headers=alice_headers)
    assert still_there.status_code == 200


def test_user_cannot_delete_another_users_source(client, auth_headers):
    alice_headers = auth_headers("alice@example.com", "alicepassword")
    bob_headers = auth_headers("bob@example.com", "bobpassword")

    alice_supplement = _create_supplement(client, alice_headers)
    source_res = client.post(
        f"/supplements/{alice_supplement['id']}/sources",
        headers=alice_headers,
        json={"name": "Costco"},
    )
    source_id = source_res.json()["sources"][0]["id"]

    res = client.delete(f"/sources/{source_id}", headers=bob_headers)
    assert res.status_code == 404


def test_restock_updates_start_date(client, auth_headers):
    headers = auth_headers()
    supplement = _create_supplement(client, headers)

    res = client.post(f"/supplements/{supplement['id']}/restock", headers=headers)
    assert res.status_code == 200
    assert res.json()["days_remaining"] == 90  # freshly restocked, full 90 days


def test_weekly_frequency_computes_correctly(client, auth_headers):
    from datetime import date

    headers = auth_headers()
    res = client.post(
        "/supplements",
        headers=headers,
        json={
            "name": "Vitamin B12 Shot",
            "start_date": date.today().isoformat(),
            "total_doses": 10,
            "dose_amount": 1,
            "frequency_count": 1,
            "frequency_unit": "week",
        },
    )
    assert res.status_code == 201
    body = res.json()
    # 10 doses, 1/week -> 70 days of supply, none elapsed yet (started today).
    assert body["days_remaining"] == 70
    assert body["frequency_unit"] == "week"
