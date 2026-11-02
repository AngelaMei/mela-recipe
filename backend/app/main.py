from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .routers import auth, export, grocery, parse, photos, recipes

app = FastAPI(title="Mela API", docs_url="/api/docs", openapi_url="/api/openapi.json")

for r in (auth.router, parse.router, recipes.router, grocery.router, photos.router, export.router):
    app.include_router(r)


@app.get("/api/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}


@app.get("/api/readyz", include_in_schema=False)
def readyz(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}
