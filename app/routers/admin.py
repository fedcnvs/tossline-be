from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import LoginPin, User, VideoOpen

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.level != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


@router.get("/db")
def view_db(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id.desc()).all()
    # eager-load the user: both tables show the email, and without this each
    # row would fire its own SELECT (500 of them for video opens).
    login_pins = (
        db.query(LoginPin)
        .options(joinedload(LoginPin.user))
        .order_by(LoginPin.id.desc())
        .limit(200)
        .all()
    )
    video_opens = (
        db.query(VideoOpen)
        .options(joinedload(VideoOpen.user))
        .order_by(VideoOpen.id.desc())
        .limit(500)
        .all()
    )
    return templates.TemplateResponse(
        "admin_db.html",
        {
            "request": request,
            "user": user,
            "users": users,
            "login_pins": login_pins,
            "video_opens": video_opens,
        },
    )
