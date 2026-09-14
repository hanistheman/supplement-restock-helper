from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import crud
import logic
from database import get_db
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

# Schema is now managed by Alembic migrations (see alembic/), not by
# create_all() — run `alembic upgrade head` before starting the app.
app = FastAPI(title="Supplement Restock Tracker")

# Allows the React dev server (different origin/port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already registered")
    db_user = crud.create_user(db, email=user.email, hashed_password=hash_password(user.password))
    return db_user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm expects fields named "username"/"password"
    # (an OAuth2 spec convention) — we treat "username" as the email here.
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.email)
    return schemas.Token(access_token=token)


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Supplements — every route below requires a valid token and only ever
# reads/writes the current user's own data.
# ---------------------------------------------------------------------------

def _to_out(s: models.Supplement) -> schemas.SupplementOut:
    """Attach the computed fields (days_remaining, restock_date, status) before returning."""
    days_left = logic.days_remaining(s.start_date, s.total_doses, s.doses_per_day)
    return schemas.SupplementOut(
        id=s.id,
        name=s.name,
        start_date=s.start_date,
        total_doses=s.total_doses,
        doses_per_day=s.doses_per_day,
        notes=s.notes,
        days_remaining=days_left,
        restock_date=logic.restock_date(s.start_date, s.total_doses, s.doses_per_day),
        status=logic.status_for(days_left),
        sources=[schemas.SourceOut.model_validate(src) for src in s.sources],
    )


def _get_or_404(db: Session, supplement_id: int, user_id: int) -> models.Supplement:
    db_supplement = crud.get_supplement(db, supplement_id, user_id)
    if db_supplement is None:
        # Deliberately the same 404 whether the supplement doesn't exist at
        # all, or exists but belongs to someone else — a 403 would leak the
        # fact that the ID belongs to another user's data.
        raise HTTPException(status_code=404, detail=f"Supplement {supplement_id} not found")
    return db_supplement


@app.get("/supplements", response_model=list[schemas.SupplementOut])
def list_supplements(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return [_to_out(s) for s in crud.get_supplements(db, current_user.id)]


@app.post("/supplements", response_model=schemas.SupplementOut, status_code=201)
def create_supplement(
    supplement: schemas.SupplementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = crud.create_supplement(db, current_user.id, supplement)
    return _to_out(db_supplement)


@app.get("/supplements/{supplement_id}", response_model=schemas.SupplementOut)
def get_supplement(
    supplement_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _to_out(_get_or_404(db, supplement_id, current_user.id))


@app.put("/supplements/{supplement_id}", response_model=schemas.SupplementOut)
def update_supplement(
    supplement_id: int,
    update: schemas.SupplementUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    db_supplement = crud.update_supplement(db, db_supplement, update)
    return _to_out(db_supplement)


@app.delete("/supplements/{supplement_id}", status_code=204)
def delete_supplement(
    supplement_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    crud.delete_supplement(db, db_supplement)
    return None


@app.post("/supplements/{supplement_id}/restock", response_model=schemas.SupplementOut)
def restock_supplement(
    supplement_id: int,
    new_total_doses: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Mark a supplement as restocked today. Optionally pass new_total_doses if the new bottle size differs."""
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    db_supplement = crud.restock_supplement(db, db_supplement, new_total_doses)
    return _to_out(db_supplement)


# Sources are managed as their own sub-resource rather than folded into
# PUT /supplements/{id}, since "add one more place I can buy this" is a
# different operation from "edit this supplement's dosing info" — keeping
# them separate avoids clients having to resend the whole source list just
# to add one entry.
@app.post("/supplements/{supplement_id}/sources", response_model=schemas.SupplementOut, status_code=201)
def add_source(
    supplement_id: int,
    source: schemas.SourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    db_supplement = crud.add_source(db, db_supplement, source)
    return _to_out(db_supplement)


@app.delete("/sources/{source_id}", status_code=204)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_source = crud.get_source(db, source_id, current_user.id)
    if db_source is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    crud.delete_source(db, db_source)
    return None