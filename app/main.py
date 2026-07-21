import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, patch_schema
from app.routers import admin, auth, events, pages
from app.seed import seed_roster

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)
patch_schema()
seed_roster()

app = FastAPI(title="Tossline BE")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(pages.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
