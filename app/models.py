from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    # naive UTC: SQLite drops tzinfo on read, so store naive throughout to
    # keep every datetime in this app directly comparable.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    login_pins: Mapped[list["LoginPin"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LoginPin(Base):
    __tablename__ = "login_pins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    pin_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="login_pins")
