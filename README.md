# tossline-be

FastAPI backend: email-PIN login + a small website with a video player.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000

## Auth flow

1. `POST /auth/request-pin {email}` — creates the user if needed, generates a
   6-digit PIN (10 min expiry), sends it via the configured email backend.
2. `POST /auth/verify-pin {email, pin}` — verifies the PIN, sets an httpOnly
   JWT session cookie.
3. `GET /auth/me` — current user (requires cookie).
4. `POST /auth/logout` — clears the cookie.

### Email backend

Controlled by `EMAIL_BACKEND` in `.env`:
- `console` (default) — PIN is logged to the server console, nothing is sent.
- `resend` — sends via [Resend](https://resend.com); set `RESEND_API_KEY` and
  `EMAIL_FROM`.

## Pages

- `/` — landing page, links to login, API docs, and health status.
- `/login` — login page (email → PIN).
- `/player` — protected page with an HTML5 video player
  (`app/static/video/sample.mp4` is a generated placeholder clip — replace it
  with real content).
- `/docs` — Swagger UI (built into FastAPI).
- `/health` — `{"status": "ok"}`.

## Data

SQLite file (`tossline.db`, gitignored) with two tables: `users`, `login_pins`.

## Deploying to Railway

The repo already has `Procfile` and `railway.json` set up to run
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`, which is what Railway
expects (Nixpacks auto-detects Python from `requirements.txt`).

1. Push this repo to GitHub (remote `origin` is already set to
   `fedcnvs/tossline-be`) and create a new Railway project from it, or run
   `railway up` from this directory with the Railway CLI.
2. In the Railway project's Variables tab, set at minimum:
   - `ENVIRONMENT=production` (makes the session cookie `Secure`, required
     since Railway serves over HTTPS)
   - `JWT_SECRET` — a real random secret, e.g. `openssl rand -hex 32`.
     Don't ship the default from `.env.example`.
   - `EMAIL_BACKEND=resend`, `RESEND_API_KEY`, `EMAIL_FROM` once Resend is
     wired up (leave as `console` and check `railway logs` in the meantime).
   - `PIN_EXPIRE_MINUTES`, `JWT_EXPIRE_MINUTES` if you want non-default
     values.
3. **SQLite caveat**: Railway's default filesystem is ephemeral — it's wiped
   on every redeploy, so the default `DATABASE_URL=sqlite:///./tossline.db`
   will lose all users/sessions on each deploy. Either:
   - Attach a [Railway volume](https://docs.railway.app/reference/volumes)
     mounted at e.g. `/data` and set `DATABASE_URL=sqlite:////data/tossline.db`, or
   - Add a Railway Postgres plugin and point `DATABASE_URL` at it (would also
     need `psycopg2-binary` added to `requirements.txt`).
4. Deploy. Railway sets `$PORT` automatically; no code changes needed.
