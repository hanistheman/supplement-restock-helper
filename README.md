# Supplement Tracker — Backend

FastAPI + SQLAlchemy + SQLite REST API for tracking supplement restock timing.

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs (Swagger UI): http://127.0.0.1:8000/docs
- Alt docs (ReDoc): http://127.0.0.1:8000/redoc

A `supplements.db` SQLite file is created automatically on first run.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/supplements` | List all supplements with computed days_remaining/status |
| POST | `/supplements` | Create a new supplement |
| GET | `/supplements/{id}` | Get one supplement |
| PUT | `/supplements/{id}` | Partially update a supplement |
| DELETE | `/supplements/{id}` | Delete a supplement |
| POST | `/supplements/{id}/restock` | Reset start_date to today (optionally pass `?new_total_doses=N`) |

## File layout

- `database.py` — SQLAlchemy engine/session setup
- `models.py` — ORM table definitions
- `schemas.py` — Pydantic request/response contracts
- `crud.py` — DB read/write functions
- `logic.py` — pure date-math (days_remaining, restock_date, status) — unit test this directly
- `main.py` — FastAPI app and route handlers