from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import backend.models as models
import backend.schemas as schemas
import backend.crud as crud
import backend.logic as logic
from backend.database import engine, get_db, Base

# Creates tables on startup if they don't exist yet. Fine for a solo project;
# for a real app with evolving schema you'd reach for Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Supplement Restock Tracker")

# Allows the React dev server (different origin/port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    )


def _get_or_404(db: Session, supplement_id: int) -> models.Supplement:
    db_supplement = crud.get_supplement(db, supplement_id)
    if db_supplement is None:
        raise HTTPException(status_code=404, detail=f"Supplement {supplement_id} not found")
    return db_supplement


@app.get("/supplements", response_model=list[schemas.SupplementOut])
def list_supplements(db: Session = Depends(get_db)):
    return [_to_out(s) for s in crud.get_supplements(db)]


@app.post("/supplements", response_model=schemas.SupplementOut, status_code=201)
def create_supplement(supplement: schemas.SupplementCreate, db: Session = Depends(get_db)):
    db_supplement = crud.create_supplement(db, supplement)
    return _to_out(db_supplement)


@app.get("/supplements/{supplement_id}", response_model=schemas.SupplementOut)
def get_supplement(supplement_id: int, db: Session = Depends(get_db)):
    return _to_out(_get_or_404(db, supplement_id))


@app.put("/supplements/{supplement_id}", response_model=schemas.SupplementOut)
def update_supplement(supplement_id: int, update: schemas.SupplementUpdate, db: Session = Depends(get_db)):
    db_supplement = _get_or_404(db, supplement_id)
    db_supplement = crud.update_supplement(db, db_supplement, update)
    return _to_out(db_supplement)


@app.delete("/supplements/{supplement_id}", status_code=204)
def delete_supplement(supplement_id: int, db: Session = Depends(get_db)):
    db_supplement = _get_or_404(db, supplement_id)
    crud.delete_supplement(db, db_supplement)
    return None


@app.post("/supplements/{supplement_id}/restock", response_model=schemas.SupplementOut)
def restock_supplement(supplement_id: int, new_total_doses: int | None = None, db: Session = Depends(get_db)):
    """Mark a supplement as restocked today. Optionally pass new_total_doses if the new bottle size differs."""
    db_supplement = _get_or_404(db, supplement_id)
    db_supplement = crud.restock_supplement(db, db_supplement, new_total_doses)
    return _to_out(db_supplement)