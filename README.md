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

Controlled by `EMAIL_BACKEND` in `.env` (code default: `resend`):
- `resend` (default) — sends via [Resend](https://resend.com); requires
  `RESEND_API_KEY`. `EMAIL_FROM` defaults to `login@evervolley.com`
  (evervolley.com is verified in Resend).
- `console` — PIN is only logged to the server console, nothing is sent.
  `.env.example` sets this for local dev so you don't need a real Resend key
  to test the login flow.

## Pages

- `/` — landing page, links to login, API docs, and health status.
- `/login` — login page (email → PIN).
- `/player` — protected page with an HTML5 video player
  (`app/static/video/sample.mp4` is a generated placeholder clip — replace it
  with real content).
- `/profile` — logged-in user's email, level, and signup date.
- `/docs` — Swagger UI (built into FastAPI).
- `/health` — `{"status": "ok"}`.
- `/admin/db` — read-only table dump of `users` and `login_pins`. Requires
  being logged in (via `/login`) with a `users.level` of `admin`; anyone else
  gets a 403, and the link is hidden from non-admins.

### Front end

Server-rendered Jinja templates, no build step. `base.html` holds the shared
head/shell and every page extends it; `_nav.html` is the signed-in topbar
(include it with `{% with active = '<page>' %}` to light up the current tab).

All styling lives in `app/static/css/style.css` — a single sheet built on CSS
custom properties (see `:root`). The look is "night court": deep court navy,
Mikasa-ball yellow accent, Anton for display type, JetBrains Mono for
data/labels, Chivo for body. Fonts come from Google Fonts at runtime.

## Data

SQLite file (`tossline.db`, gitignored) with two tables: `users`, `login_pins`.

### User levels

`users.level` defaults to `"user"`. Whoever logs in with the email matching
`ADMIN_EMAIL` (defaults to federico.cian@gmail.com) is automatically
promoted to `"admin"` on their next `request-pin` call — no manual DB edit
needed. To promote someone else, either change `ADMIN_EMAIL` or update their
row directly (`UPDATE users SET level='admin' WHERE id=...`).

Existing databases (e.g. the one on a Railway volume) get the `level` column
added automatically on startup via `patch_schema()` in `app/database.py` —
`Base.metadata.create_all` only creates missing tables, not columns on
tables that already exist.

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
   - `RESEND_API_KEY` — `EMAIL_BACKEND` and `EMAIL_FROM` already default to
     `resend` / `login@evervolley.com` in code, so PINs will actually send
     once the key is set.
   - `PIN_EXPIRE_MINUTES`, `JWT_EXPIRE_MINUTES` if you want non-default
     values.
   - `ADMIN_EMAIL` if it should differ from the default
     (federico.cian@gmail.com).
3. **SQLite caveat**: Railway's default filesystem is ephemeral — it's wiped
   on every redeploy, so the default `DATABASE_URL=sqlite:///./tossline.db`
   will lose all users/sessions on each deploy. Either:
   - Attach a [Railway volume](https://docs.railway.app/reference/volumes)
     mounted at e.g. `/data` and set `DATABASE_URL=sqlite:////data/tossline.db`, or
   - Add a Railway Postgres plugin and point `DATABASE_URL` at it (would also
     need `psycopg2-binary` added to `requirements.txt`).
4. Deploy. Railway sets `$PORT` automatically; no code changes needed.
