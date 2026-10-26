import json
from urllib.parse import urlencode

import pytest
from django.test import Client
from django.core.cache import cache


class ApiClient(Client):
    """Django test client with the JSON keyword used by the API tests."""
    def post(self, path, data=None, content_type="application/json", **kwargs):
        if "json" in kwargs:
            data = json.dumps(kwargs.pop("json"))
            content_type = "application/json"
        elif content_type == "application/x-www-form-urlencoded" and isinstance(data, dict):
            data = urlencode(data)
        return super().post(path, data=data, content_type=content_type, **kwargs)

    def put(self, path, data=None, content_type="application/json", **kwargs):
        if "json" in kwargs:
            data = json.dumps(kwargs.pop("json"))
            content_type = "application/json"
        return super().put(path, data=data, content_type=content_type, **kwargs)

    def patch(self, path, data=None, content_type="application/json", **kwargs):
        if "json" in kwargs:
            data = json.dumps(kwargs.pop("json"))
            content_type = "application/json"
        return super().patch(path, data=data, content_type=content_type, **kwargs)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    cache.clear()


@pytest.fixture
def client():
    return ApiClient()


@pytest.fixture
def auth_headers(client):
    def make(email="test@example.com", password="testpassword123"):
        client.post("/auth/register", json={"email": email, "password": password})
        response = client.post("/auth/login", data={"username": email, "password": password}, content_type="application/x-www-form-urlencoded")
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    return make


@pytest.fixture
def auth_tokens(client):
    def make(email="test@example.com", password="testpassword123"):
        client.post("/auth/register", json={"email": email, "password": password})
        return client.post("/auth/login", data={"username": email, "password": password}, content_type="application/x-www-form-urlencoded").json()
    return make
