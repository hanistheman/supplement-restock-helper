"""
Shared pytest fixtures for API tests.

Uses a separate `supplement_tracker_test` Postgres database (never the dev
database) so running tests can't ever wipe or pollute real data. Tables are
created fresh per test session and each test runs inside its own set of
rows cleaned up afterward via truncation.
"""
import os

# Point the app at the test database BEFORE importing any app modules,
# since database.py reads DATABASE_URL at import time.
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/supplement_tracker_test"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
import models  # noqa: F401 — registers models on Base.metadata

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    """Create all tables once for the test session, drop them afterward."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables between tests so each test starts with a clean slate."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers a fresh user and returns headers with a valid bearer token."""
    def _make(email="test@example.com", password="testpassword123"):
        client.post("/auth/register", json={"email": email, "password": password})
        res = client.post("/auth/login", data={"username": email, "password": password})
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
