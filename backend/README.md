# Supplement Tracker backend

Django REST Framework API using Django's ORM and migration system. The React client keeps using the existing routes and bearer token format.

## Start locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

The API listens on `http://127.0.0.1:8000`. PostgreSQL is available through `docker compose up -d`; configure `DATABASE_URL` to point to it. If `DATABASE_URL` is omitted, Django uses `backend/db.sqlite3`.

## Existing PostgreSQL database

The Django initial migration uses the existing `users`, `refresh_tokens`, `supplements`, and `sources` table names. For a database that already has those tables, back it up, review its schema, and run `python manage.py migrate --fake-initial` to record the initial migration. If that database already has a `skipped_days` table, record the skipped-day migrsation with `python manage.py migrate tracker 0002 --fake`; otherwise, apply it normally with `python manage.py migrate`.

Create future schema changes with `python manage.py makemigrations` and apply them with `python manage.py migrate`.

## Tests and CI

Install the development dependencies and run the suite from `backend/`:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The tests use Django's isolated test database. SQLite is the default when `DATABASE_URL` is not set, so local tests and GitHub Actions do not need a running PostgreSQL service. The workflow at `.github/workflows/backend-tests.yml` runs Django system checks, verifies migration files are current, and runs the full suite on pushes and pull requests that touch the backend.

## Configuration

Copy `.env.example` to `.env`. `SECRET_KEY` signs the 15-minute access tokens; refresh tokens are random, single-use values stored by SHA-256 hash for 30 days. Set `DJANGO_DEBUG=false` and a production secret before deployment. `NOTIFICATIONS_SECRET` protects the scheduled low-stock check. SMTP settings enable real mail; if `SMTP_HOST` is empty, notifications are printed to the server console.

## API

Auth endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, and `PATCH /auth/me/notifications`.

Supplement endpoints: `GET/POST /supplements`, `GET/PUT/DELETE /supplements/{id}`, `POST /supplements/{id}/restock`, `POST /supplements/{id}/sources`, `DELETE /sources/{id}`, plus scheduler-only `POST /notifications/run`.

Skipped-dose endpoints: `POST /supplements/{id}/skipped-days` with `{"date":"YYYY-MM-DD"}` and `DELETE /supplements/{id}/skipped-days/{skipped_day_id}`. Each missed scheduled dose extends the projected supply by one scheduled dosing interval. Restocking clears the skipped dates from the previous bottle.

Login accepts the existing form-encoded `username`/`password` contract (email is used as username). Auth register/login are limited to five requests per minute per IP using Django's local memory cache; for multiple workers, configure a shared Django cache backend.
