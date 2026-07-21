from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import LoginPin, User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def require_admin(user: User = Depends(get_current_user)) -> None:
    if user.email.lower() != settings.admin_email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("/db")
def view_db(request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    users = db.query(User).order_by(User.id.desc()).all()
    login_pins = db.query(LoginPin).order_by(LoginPin.id.desc()).limit(200).all()
    return templates.TemplateResponse(
        "admin_db.html",
        {"request": request, "users": users, "login_pins": login_pins},
    )
