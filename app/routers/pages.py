from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_optional_user
from app.models import User

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/player")
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/player")
def player_page(request: Request, user: User | None = Depends(get_optional_user)):
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("player.html", {"request": request, "user": user})
