"""Seed the invite-only roster.

Tossline is closed: `POST /auth/request-pin` only issues a code to an email
that already has a row in `users`. This module makes sure the roster below
exists on every startup.

It is additive and idempotent: it inserts missing people, promotes anyone
listed in ADMIN_EMAILS who isn't an admin yet, and never demotes or deletes.
So a promotion you make by hand in the DB survives a redeploy. Adding someone
later does NOT require editing this file; inserting a row in `users` is enough.
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

# Anyone here gets level="admin" — i.e. read access to every user's email
# and login-code history on /admin/db. `settings.admin_email` is always
# included on top of this.
ADMIN_EMAILS = {
    "conivafer23@gmail.com",
}


def admin_emails() -> set[str]:
    return {e.strip().lower() for e in ADMIN_EMAILS | {settings.admin_email} if e.strip()}


def find_user(db: Session, email: str) -> User | None:
    """Look a user up case-insensitively — several roster addresses were
    supplied with capitals, but people type their email in lower case."""
    return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()


def seed_roster() -> None:
    db = SessionLocal()
    try:
        admins = admin_emails()
        # Collapse to one entry per email before touching the DB. An address
        # can appear in both ROSTER and the admin set (e.g. conivafer23), and
        # admin_emails() adds settings.admin_email on top — inserting the same
        # email twice would trip the UNIQUE constraint on a fresh database.
        desired: dict[str, str | None] = {}
        for name, email in ROSTER:
            desired.setdefault(email.strip().lower(), name)
        for email in admins:  # ensures every admin can get in, even on a fresh DB
            desired.setdefault(email, None)

        added = 0
        promoted = 0

        for email, name in desired.items():
            existing = find_user(db, email)

            if existing is None:
                db.add(User(email=email, name=name, level="admin" if email in admins else "user"))
                added += 1
            elif email in admins and existing.level != "admin":
                # Covers roster members already inserted as plain users on a
                # deployed DB — changing the list above alone wouldn't reach them.
                existing.level = "admin"
                promoted += 1

        if added or promoted:
            db.commit()
            logger.info("Seed: %s user(s) added, %s promoted to admin", added, promoted)
    finally:
        db.close()
