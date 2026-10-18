"""
SQLAlchemy ORM models — these map directly to database tables.

Note this is separate from schemas.py (Pydantic). That split is intentional:
- models.py   = what's stored in the DB
- schemas.py  = what's sent/received over the API
They often look similar but they don't have to match, and keeping them
separate means you can change your DB schema without automatically
changing your API contract (and vice versa).
"""
from sqlalchemy import Integer, String, Float, Date, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplements: Mapped[list["Supplement"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    Stores only a SHA-256 hash of the refresh token, never the raw value —
    same principle as password storage. If the database were ever leaked,
    the hashes alone can't be used to log in as anyone. Revoked/expired
    tokens are kept (not deleted) so there's an audit trail of token use.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    expires_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship()


class Supplement(Base):
    __tablename__ = "supplements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    total_doses: Mapped[int] = mapped_column(Integer, nullable=False)
    # How often the supplement is taken: "take {dose_amount} doses,
    # {frequency_count} times per {frequency_unit}" — e.g. 2 capsules, 3
    # times per week. doses_per_day is derived from these at read time
    # (see logic.doses_per_day_from_frequency), not stored, consistent with
    # how days_remaining/restock_date/status are already computed on read.
    dose_amount: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    frequency_count: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    frequency_unit: Mapped[str] = mapped_column(String, nullable=False, default="day")
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="supplements")
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
