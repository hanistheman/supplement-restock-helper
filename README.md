# Supplement Restock Tracker

A full-stack app for tracking when you'll run out of supplements, so you know when to restock — before you're standing at an empty bottle.

Built as a learning project for REST API design (FastAPI + SQLAlchemy) and a React frontend.

## How it works

For each supplement, you log:
- When you started the current bottle
- How many total doses are in it
- How many doses you take per day

The app computes days remaining and a restock-by date, and flags anything running low, critical, or overdue — no manual logging of each dose required.

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, SQLite |
| Frontend | React (Vite) |
| API docs | Auto-generated via FastAPI (Swagger UI + ReDoc) |

## Project structure

```
supplement-restock-predictor/
├── backend/          # FastAPI REST API + SQLite database
│   ├── main.py        # App entrypoint, route handlers
│   ├── database.py    # SQLAlchemy engine/session setup
│   ├── models.py       # ORM table definitions
│   ├── schemas.py      # Pydantic request/response schemas
│   ├── crud.py          # DB read/write operations
│   ├── logic.py          # Days-remaining / restock-date calculations
│   └── requirements.txt
└── frontend/          # React (Vite) single-page app
    ├── src/
    │   ├── api.js           # Fetch wrapper for backend calls
    │   ├── App.jsx           # Top-level state and layout
    │   └── components/       # SupplementList, SupplementCard, SupplementForm
    └── package.json
```

## Getting started

You'll need [Python 3.10+](https://www.python.org/downloads/) and [Node.js 18+](https://nodejs.org/) installed.

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. A `supplements.db` SQLite file is created automatically on first run. Interactive API docs are at `http://127.0.0.1:8000/docs`.

### 2. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend expects the backend to be running at `http://127.0.0.1:8000` (configurable in `frontend/src/api.js`).

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/supplements` | List all supplements, with computed `days_remaining` and `status` |
| `POST` | `/supplements` | Add a new supplement |
| `GET` | `/supplements/{id}` | Get one supplement |
| `PUT` | `/supplements/{id}` | Update a supplement (partial updates supported) |
| `DELETE` | `/supplements/{id}` | Remove a supplement |
| `POST` | `/supplements/{id}/restock` | Reset the start date to today (optionally pass `?new_total_doses=N` for a new bottle size) |

Full request/response schemas are viewable at `/docs` while the backend is running.

## Status thresholds

| Status | Condition |
|---|---|
| `ok` | More than 7 days of supply left |
| `low` | 4–7 days left |
| `critical` | 0–3 days left |
| `overdue` | Past the restock date |

## Roadmap / ideas

- [ ] Notifications/reminders before running out
- [ ] Sort/filter by status or name
- [ ] Multi-user support with auth
- [ ] Deploy backend + frontend so it's usable outside localhost