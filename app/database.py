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
    additions = []
    if "level" not in columns:
        additions.append("ALTER TABLE users ADD COLUMN level VARCHAR NOT NULL DEFAULT 'user'")
    if "name" not in columns:
        additions.append("ALTER TABLE users ADD COLUMN name VARCHAR")

    if additions:
        with engine.begin() as conn:
            for statement in additions:
                conn.execute(text(statement))
