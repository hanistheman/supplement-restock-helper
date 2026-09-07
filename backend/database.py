"""
Database connection setup.

Reads the connection string from the DATABASE_URL environment variable
(via a .env file locally) so the same code works against local Postgres,
a managed cloud Postgres instance, or (with a different URL) any other
SQLAlchemy-supported database, without code changes.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in "
        "your connection string."
    )

# connect_args is SQLite-specific (check_same_thread); Postgres doesn't
# need it, so we only pass it when the URL is actually SQLite. This keeps
# the file usable as a fallback for quick local experiments without Docker.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """All ORM models inherit from this."""
    pass


def get_db():
    """
    FastAPI dependency that provides a DB session per request and always
    closes it afterward, even if the request raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
