""" Database connection setup. 

This is where we handle SQLite. 
Should we switch to another database, like Postgres, 
we change this. All other stuff talks to SQLAlchemy.  
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./supplements.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """All ORM models inherit from here."""
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
