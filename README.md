# Supplement Restock Tracker

A full-stack app for tracking when you'll run out of supplements, so you know when to restock — before you're standing at an empty bottle.

Built as a learning project using Django REST Framework and a React frontend.

## How it works

For each supplement, you log:
- When you started the current bottle
- How many total doses are in it
- How many doses you take per day

The app computes days remaining and a restock-by date, and flags anything running low, critical, or overdue — no manual logging of each dose required.

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python, Django REST Framework, Django ORM, PostgreSQL, Django migrations, JWT auth (bcrypt + python-jose) |
| Frontend | React (Vite) |
| API | Django REST Framework |

## Project structure

```
supplement-restock-predictor/
├── backend/          # Django REST API + PostgreSQL database
│   ├── manage.py       # Django management entrypoint
│   ├── config/         # Django settings, URLs, WSGI
│   ├── tracker/        # ORM models, API views, authentication, migrations
│   ├── logic.py        # Days-remaining / restock-date calculations
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
python manage.py migrate
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000`. See `backend/README.md` for PostgreSQL setup and database migration notes (Docker Compose is included for local development).

### 2. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend expects the backend to be running at `http://127.0.0.1:8000` (configurable in `frontend/src/api.js`).

## Accounts

Each user has their own private set of supplements — sign up, log in, and only you can see or modify your own data. See `backend/README.md` for the auth endpoints and how tokens work.

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/supplements` | List all supplements, with computed `days_remaining` and `status` |
| `POST` | `/supplements` | Add a new supplement |
| `GET` | `/supplements/{id}` | Get one supplement |
| `PUT` | `/supplements/{id}` | Update a supplement (partial updates supported) |
| `DELETE` | `/supplements/{id}` | Remove a supplement |
| `POST` | `/supplements/{id}/restock` | Reset the start date to today (optionally pass `?new_total_doses=N` for a new bottle size) |


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
- [ ] Deploy backend + frontend so it's usable outside localhost
