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

The initial Django migration uses the existing `users`, `refresh_tokens`, `supplements`, and `sources` table names. Back up the database, then run `python manage.py migrate --fake-initial` to record the initial migration when those tables already exist. Review the live schema before doing this: the command marks the migration as applied without changing existing tables. New installs use `python manage.py migrate` normally.

Create future schema changes with `python manage.py makemigrations` and apply them with `python manage.py migrate`.

## Configuration

Copy `.env.example` to `.env`. `SECRET_KEY` signs the 15-minute access tokens; refresh tokens are random, single-use values stored by SHA-256 hash for 30 days. Set `DJANGO_DEBUG=false` and a production secret before deployment. `NOTIFICATIONS_SECRET` protects the scheduled low-stock check. SMTP settings enable real mail; if `SMTP_HOST` is empty, notifications are printed to the server console.

## API

Auth endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, and `PATCH /auth/me/notifications`.

Supplement endpoints: `GET/POST /supplements`, `GET/PUT/DELETE /supplements/{id}`, `POST /supplements/{id}/restock`, `POST /supplements/{id}/sources`, `DELETE /sources/{id}`, plus scheduler-only `POST /notifications/run`.

Login accepts the existing form-encoded `username`/`password` contract (email is used as username). Auth register/login are limited to five requests per minute per IP using Django's local memory cache; for multiple workers, configure a shared Django cache backend.
