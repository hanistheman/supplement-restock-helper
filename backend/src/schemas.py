"""
Pydantic schemas — these define what goes over the wire (request bodies and
JSON responses), separate from the DB model (models.py).

Naming convention used here:
- SupplementBase   -> shared fields
- SupplementCreate -> what the client sends on POST
- SupplementUpdate -> what the client sends on PUT (all fields optional)
- SupplementOut    -> what the API returns (adds id + computed fields)
"""
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class SupplementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    total_doses: int = Field(..., gt=0)
    doses_per_day: float = Field(default=1.0, gt=0)
    notes: str | None = None


class SupplementCreate(SupplementBase):
    pass


class SupplementUpdate(BaseModel):
    """All fields optional, since PUT here is used for partial-friendly edits."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_date: date | None = None
    total_doses: int | None = Field(default=None, gt=0)
    doses_per_day: float | None = Field(default=None, gt=0)
    notes: str | None = None


class SupplementOut(SupplementBase):
    id: int
    days_remaining: int
    restock_date: date
    status: str

    # Lets Pydantic build this schema directly from a SQLAlchemy ORM object
    # (model.name, model.id, etc.) rather than requiring a dict.
    model_config = ConfigDict(from_attributes=True)