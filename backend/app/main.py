import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .routers import auth, export, grocery, parse, photos, recipes

log = logging.getLogger("mela")


def config_problems() -> list[str]:
    """Settings that would break sign-in. Checked at startup so a bad secret fails the deploy, not the login."""
    s = get_settings()
    problems = []
    if len(s.session_secret) < 16:
        problems.append(f"SESSION_SECRET is {len(s.session_secret)} characters; it needs at least 16 (try: openssl rand -base64 32)")
    if not s.mela_passcode:
        problems.append("MELA_PASSCODE is empty")
    if not s.members:
        problems.append("MELA_MEMBERS is empty")
    return problems


@asynccontextmanager
async def lifespan(_app: FastAPI):
    problems = config_problems()
    if problems:
        for p in problems:
            log.error("Configuration error: %s", p)
        raise RuntimeError("Mela can't start: " + "; ".join(problems))
    yield


app = FastAPI(title="Mela API", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)

for r in (auth.router, parse.router, recipes.router, grocery.router, photos.router, export.router):
    app.include_router(r)


@app.get("/api/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}


@app.get("/api/readyz", include_in_schema=False)
def readyz(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}
