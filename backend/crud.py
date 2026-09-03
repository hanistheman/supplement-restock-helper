"""
CRUD layer — functions that talk to the DB via a SQLAlchemy session.

Keeping these separate from main.py means your route handlers stay thin
(parse request -> call crud function -> return response) and your DB
queries are reusable/testable without needing a running API.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
import models
import schemas


def get_supplement(db: Session, supplement_id: int) -> models.Supplement | None:
    return db.get(models.Supplement, supplement_id)


def get_supplements(db: Session) -> list[models.Supplement]:
    return list(db.scalars(select(models.Supplement)))


def create_supplement(db: Session, supplement: schemas.SupplementCreate) -> models.Supplement:
    data = supplement.model_dump(exclude={"sources"})
    db_supplement = models.Supplement(**data)
    # Convert each SourceCreate into a Source row and attach via the
    # relationship — SQLAlchemy handles the supplement_id FK automatically
    # once this object is added to the session.
    for source in supplement.sources:
        db_supplement.sources.append(models.Source(name=source.name, url=str(source.url) if source.url else None))
    db.add(db_supplement)
    db.commit()
    db.refresh(db_supplement)
    return db_supplement


def add_source(db: Session, db_supplement: models.Supplement, source: schemas.SourceCreate) -> models.Supplement:
    db_supplement.sources.append(
        models.Source(name=source.name, url=str(source.url) if source.url else None)
    )
    db.commit()
    db.refresh(db_supplement)
    return db_supplement


def get_source(db: Session, source_id: int) -> models.Source | None:
    return db.get(models.Source, source_id)


def delete_source(db: Session, db_source: models.Source) -> None:
    db.delete(db_source)
    db.commit()


def update_supplement(
    db: Session, db_supplement: models.Supplement, update: schemas.SupplementUpdate
) -> models.Supplement:
    # Only overwrite fields the client actually sent.
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_supplement, field, value)
    db.commit()
    db.refresh(db_supplement)
    return db_supplement


def delete_supplement(db: Session, db_supplement: models.Supplement) -> None:
    db.delete(db_supplement)
    db.commit()


def restock_supplement(db: Session, db_supplement: models.Supplement, new_total_doses: int | None = None) -> models.Supplement:
    """Reset start_date to today; optionally update total_doses (new bottle size)."""
    from datetime import date
    db_supplement.start_date = date.today()
    if new_total_doses is not None:
        db_supplement.total_doses = new_total_doses
    db.commit()
    db.refresh(db_supplement)
    return db_supplement