"""Seed the invite-only roster.

Tossline is closed: `POST /auth/request-pin` only issues a code to an email
that already has a row in `users`. This module makes sure the roster below
exists on every startup.

It is additive and idempotent — it inserts missing people and never updates
or deletes existing rows, so promoting someone to admin by hand in the DB
survives a redeploy. Adding someone later does NOT require editing this
file; inserting a row in `users` is enough.
"""

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import User

logger = logging.getLogger("tossline.seed")

# (name, email) — name is None where we weren't given one.
ROSTER: list[tuple[str | None, str]] = [
    ("Pardo Mati", "pardomati2@gmail.com"),
    ("Fabio Balaso", "balaso.fabio@gmail.com"),
    ("Yuri Romanò", "yuri3@hotmail.it"),
    ("Roberto Russo", "russo.roby97@yahoo.it"),
    ("Simone Giannelli", "simone-giannelli@hotmail.it"),
    ("Mattia Bottolo", "mattiabottolo@gmail.com"),
    ("Alessandro Bovolenta", "alessandrobovo04@gmail.com"),
    ("Gianluca Galassi", "gianlucagalassi@hotmail.it"),
    ("Gabriele Laurenzano", "gabriele.laurenzano1@libero.it"),
    ("Daniele Lavia", "danielelavia1@gmail.com"),
    ("Luca Porro", "luchinoporro@gmail.com"),
    ("Giovanni Sanguinetti", "giovannisanguinetti34@gmail.com"),
    ("Francesco Sani", "francesco.romano.sani@gmail.com"),
    ("Riccardo Sbertoli", "rickysb6@gmail.com"),
    (None, "ferdidegiorgi@libero.it"),
    (None, "marcomeoni@yahoo.it"),
    (None, "albisalmaso95@gmail.com"),
    (None, "conivafer23@gmail.com"),
]


def find_user(db: Session, email: str) -> User | None:
    """Look a user up case-insensitively — several roster addresses were
    supplied with capitals, but people type their email in lower case."""
    return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()


def seed_roster() -> None:
    db = SessionLocal()
    try:
        # The admin must always be able to get in, even on a fresh database,
        # or nobody can reach /admin/db to fix anything.
        entries = ROSTER + [(None, settings.admin_email)]
        added = 0

        for name, email in entries:
            email = email.strip().lower()
            if find_user(db, email):
                continue

            level = "admin" if email == settings.admin_email.strip().lower() else "user"
            db.add(User(email=email, name=name, level=level))
            added += 1

        if added:
            db.commit()
            logger.info("Seeded %s roster user(s)", added)
    finally:
        db.close()
