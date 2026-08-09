"""SQLAlchemy ORM models - map directly to database tables. 

Separate from schemas.py
- models.py = what's stored in the database
- schemas.py = what's sent/received via the API

They look similar, but don't have to match. 
Keeping them separate allows for flexibility with changing DB schema without 
automatic changes to API contract (and vice versa). 
"""

from sqlalchemy import Integer, String, Float, Date
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Supplement(Base):
    __tablename__ = "supplements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    total_doses: Mapped[int] = mapped_column(Integer, nullable=False)
    doses_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
