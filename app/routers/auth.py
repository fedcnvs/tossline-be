from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.email_service import send_pin_email
from app.models import LoginPin, User, utcnow
from app.schemas import RequestPinIn, UserOut, VerifyPinIn
from app.seed import find_user
from app.security import COOKIE_NAME, create_access_token, generate_pin, hash_pin, verify_pin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-pin", status_code=status.HTTP_204_NO_CONTENT)
def request_pin(payload: RequestPinIn, db: Session = Depends(get_db)):
    # Invite-only: we never create users here. A row must already exist,
    # seeded from app/seed.py or inserted by hand.
    user = find_user(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This email isn't on the invite list.",
        )

    if user.email.lower() == settings.admin_email.lower() and user.level != "admin":
        user.level = "admin"
        db.commit()

    pin = generate_pin()
    login_pin = LoginPin(
        user_id=user.id,
        pin_hash=hash_pin(pin),
        expires_at=utcnow() + timedelta(minutes=settings.pin_expire_minutes),
    )
    db.add(login_pin)
    db.commit()

    send_pin_email(user.email, pin)


@router.post("/verify-pin", response_model=UserOut)
def verify_pin_endpoint(payload: VerifyPinIn, response: Response, db: Session = Depends(get_db)):
    user = find_user(db, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or PIN")

    login_pin = (
        db.query(LoginPin)
        .filter(LoginPin.user_id == user.id, LoginPin.consumed.is_(False))
        .order_by(LoginPin.created_at.desc())
        .first()
    )

    now = utcnow()
    if (
        not login_pin
        or login_pin.expires_at < now
        or not verify_pin(payload.pin, login_pin.pin_hash)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or PIN")

    login_pin.consumed = True
    db.commit()

    token = create_access_token(subject=user.email)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
