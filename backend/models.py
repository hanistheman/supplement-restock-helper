"""
SQLAlchemy ORM models — these map directly to database tables.

Note this is separate from schemas.py (Pydantic). That split is intentional:
- models.py   = what's stored in the DB
- schemas.py  = what's sent/received over the API
They often look similar but they don't have to match, and keeping them
separate means you can change your DB schema without automatically
changing your API contract (and vice versa).
"""
from sqlalchemy import Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Supplement(Base):
    __tablename__ = "supplements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    total_doses: Mapped[int] = mapped_column(Integer, nullable=False)
    doses_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    sources: Mapped[list["Source"]] = relationship(
        back_populates="supplement", cascade="all, delete-orphan", order_by="Source.id"
    )


class Source(Base):
    """
    A place to buy a given supplement — either a brick & mortar store
    (name only) or an online retailer (name + url). A supplement can have
    several of these (e.g. "cheapest at Costco, fastest on Amazon").
    """
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supplement_id: Mapped[int] = mapped_column(ForeignKey("supplements.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    supplement: Mapped["Supplement"] = relationship(back_populates="sources")
