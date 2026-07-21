from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import COOKIE_NAME, decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    email = decode_access_token(token) if token else None
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    email = decode_access_token(token) if token else None
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()
