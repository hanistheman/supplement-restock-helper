"""
Pydantic schemas — these define what goes over the wire (request bodies and
JSON responses), separate from the DB model (models.py).

Naming convention used here:
- SupplementBase   -> shared fields
- SupplementCreate -> what the client sends on POST
- SupplementUpdate -> what the client sends on PUT (all fields optional)
- SupplementOut    -> what the API returns (adds id + computed fields)
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    # HttpUrl validates the string is actually a well-formed URL, so a bad
    # link fails at the API boundary rather than silently rendering broken.
    url: HttpUrl | None = None


class SourceCreate(SourceBase):
    pass


class SourceOut(SourceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SupplementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    total_doses: int = Field(..., gt=0)
    doses_per_day: float = Field(default=1.0, gt=0)
    notes: str | None = None


class SupplementCreate(SupplementBase):
    sources: list[SourceCreate] = Field(default_factory=list)


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
    sources: list[SourceOut] = Field(default_factory=list)

    # Lets Pydantic build this schema directly from a SQLAlchemy ORM object
    # (model.name, model.id, etc.) rather than requiring a dict.
    model_config = ConfigDict(from_attributes=True)