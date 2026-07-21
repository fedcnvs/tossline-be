import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import LoginPin, User

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    valid_username = secrets.compare_digest(credentials.username, settings.admin_username)
    valid_password = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.get("/db")
def view_db(request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    users = db.query(User).order_by(User.id.desc()).all()
    login_pins = db.query(LoginPin).order_by(LoginPin.id.desc()).limit(200).all()
    return templates.TemplateResponse(
        "admin_db.html",
        {"request": request, "users": users, "login_pins": login_pins},
    )
