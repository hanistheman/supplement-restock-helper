import os
from datetime import date, timedelta

from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)
from notifications import run_low_stock_check

# Schema is now managed by Alembic migrations (see alembic/), not by
# create_all() — run `alembic upgrade head` before starting the app.
app = FastAPI(title="Supplement Restock Tracker")

# Rate limiting, keyed by client IP. Applied selectively (see /auth/login
# and /auth/register below) rather than globally — brute-force protection
# matters most on auth endpoints; a blanket limit on every route would
# punish normal use of the app (e.g. the shelf page listing + polling).
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("5/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already registered")
    db_user = crud.create_user(db, email=user.email, hashed_password=hash_password(user.password))
    return db_user


def _issue_tokens(db: Session, user: models.User) -> schemas.Token:
    access_token = create_access_token(subject=user.email)
    raw_refresh_token = generate_refresh_token()
    crud.store_refresh_token(
        db, user_id=user.id, token_hash=hash_refresh_token(raw_refresh_token), expires_at=refresh_token_expiry()
    )
    return schemas.Token(access_token=access_token, refresh_token=raw_refresh_token)


@app.post("/auth/login", response_model=schemas.Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm expects fields named "username"/"password"
    # (an OAuth2 spec convention) — we treat "username" as the email here.
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_tokens(db, user)


@app.post("/auth/refresh", response_model=schemas.Token)
def refresh(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """
    Exchanges a valid, unexpired refresh token for a new access token.
    The refresh token itself is rotated — the one presented here is
    revoked and a brand new one issued — so a refresh token can only ever
    be used once. If someone steals and replays an already-used refresh
    token, it will simply fail here, which at minimum fails safe and in a
    system with reuse-detection could flag the theft (not implemented
    here, but this rotation is the mechanism that would make that possible
    later).
    """
    token_hash = hash_refresh_token(body.refresh_token)
    db_token = crud.get_valid_refresh_token(db, token_hash)
    if db_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    crud.revoke_refresh_token(db, db_token)
    user = db.get(models.User, db_token.user_id)
    return _issue_tokens(db, user)


@app.post("/auth/logout", status_code=204)
def logout(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    """
    Revokes a specific refresh token server-side. This is what makes
    logout meaningfully different from just deleting tokens client-side:
    without this, a copied-out refresh token would keep working even
    after the user "logs out" on the device it was taken from.
    """
    token_hash = hash_refresh_token(body.refresh_token)
    db_token = crud.get_valid_refresh_token(db, token_hash)
    if db_token is not None:
        crud.revoke_refresh_token(db, db_token)
    return None


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.patch("/auth/me/notifications", response_model=schemas.UserOut)
def update_notification_settings(
    settings: schemas.NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    current_user.notifications_enabled = settings.notifications_enabled
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# Notifications — triggered externally (a scheduled job, hosted cron, etc.),
# not by a logged-in user, so this is protected by a shared secret header
# rather than the usual per-user JWT auth.
# ---------------------------------------------------------------------------

def _verify_notifications_secret(x_notifications_secret: str = Header(default="")):
    expected = os.getenv("NOTIFICATIONS_SECRET")
    if not expected or x_notifications_secret != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing notifications secret")


@app.post("/notifications/run", dependencies=[Depends(_verify_notifications_secret)])
def trigger_notifications(db: Session = Depends(get_db)):
    sent = run_low_stock_check(db)
    return {"emails_sent": sent}


# ---------------------------------------------------------------------------
# Supplements — every route below requires a valid token and only ever
# reads/writes the current user's own data.
# ---------------------------------------------------------------------------

def _to_out(s: models.Supplement) -> schemas.SupplementOut:
    """Attach the computed fields (days_remaining, restock_date, status) before returning."""
    doses_per_day = logic.doses_per_day_from_frequency(s.dose_amount, s.frequency_count, s.frequency_unit)
    skipped_count = sum(1 for entry in s.skipped_days if entry.date >= s.start_date)
    missed_interval = logic.DAYS_PER_UNIT[s.frequency_unit] / s.frequency_count
    days_left = logic.days_remaining(s.start_date, s.total_doses, doses_per_day) + round(skipped_count * missed_interval)
    return schemas.SupplementOut(
        id=s.id,
        name=s.name,
        start_date=s.start_date,
        total_doses=s.total_doses,
        dose_amount=s.dose_amount,
        frequency_count=s.frequency_count,
        frequency_unit=s.frequency_unit,
        notes=s.notes,
        days_remaining=days_left,
        restock_date=logic.restock_date(s.start_date, s.total_doses, doses_per_day) + timedelta(days=round(skipped_count * missed_interval)),
        status=logic.status_for(days_left),
        sources=[schemas.SourceOut.model_validate(src) for src in s.sources],
        skipped_days=[schemas.SkippedDayOut.model_validate(day) for day in s.skipped_days],
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


@app.post("/supplements/{supplement_id}/skipped-days", response_model=schemas.SupplementOut, status_code=201)
def add_skipped_day(
    supplement_id: int,
    skipped_day: schemas.SkippedDayCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    if skipped_day.date < db_supplement.start_date or skipped_day.date > date.today():
        raise HTTPException(status_code=422, detail="Skipped date must be between the supplement start date and today")
    if any(entry.date == skipped_day.date for entry in db_supplement.skipped_days):
        raise HTTPException(status_code=409, detail="A skipped day is already recorded for this date")
    db_supplement.skipped_days.append(models.SkippedDay(date=skipped_day.date))
    db.commit()
    db.refresh(db_supplement)
    return _to_out(db_supplement)


@app.delete("/supplements/{supplement_id}/skipped-days/{skipped_day_id}", status_code=204)
def delete_skipped_day(
    supplement_id: int,
    skipped_day_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_supplement = _get_or_404(db, supplement_id, current_user.id)
    entry = next((day for day in db_supplement.skipped_days if day.id == skipped_day_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Skipped day {skipped_day_id} not found")
    db.delete(entry)
    db.commit()
    return None


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
