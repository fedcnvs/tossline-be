from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def patch_schema():
    # Base.metadata.create_all only creates missing tables, not columns on
    # tables that already exist (e.g. the persisted DB on a Railway volume).
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("users")}
    statements = []
    if "level" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN level VARCHAR NOT NULL DEFAULT 'user'")
    if "name" not in columns:
        statements.append("ALTER TABLE users ADD COLUMN name VARCHAR")

    # "cloudflare" used to describe where the web player was hosted, but it
    # looked like a database location in the admin UI. Events have always lived
    # in this backend DB; normalize the display label to the client platform.
    if "video_opens" in inspector.get_table_names():
        statements.append("UPDATE video_opens SET source = 'web' WHERE source = 'cloudflare'")

    if statements:
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))
