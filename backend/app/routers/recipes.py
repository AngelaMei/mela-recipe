import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import current_member
from ..db import get_db
from ..models import CookLog, Photo, Recipe
from ..schemas import LogIn, LogPatch, RecipeIn, RecipePatch
from ..serialize import log_out, recipe_out, recipe_stats
from ..services import search as search_service
from ..services.lines import normalize_ingredient

router = APIRouter(prefix="/api", tags=["recipes"])


def _all_recipes(db: Session) -> list[Recipe]:
    return list(db.scalars(select(Recipe).options(selectinload(Recipe.logs))))


def _get_recipe(db: Session, recipe_id: str) -> Recipe:
    try:
        rid = uuid.UUID(recipe_id)
    except ValueError:
        raise HTTPException(404, "Recipe not found")
    recipe = db.scalars(select(Recipe).where(Recipe.id == rid).options(selectinload(Recipe.logs))).first()
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    return recipe


def _photo_id(db: Session, value: str | None) -> uuid.UUID | None:
    if not value:
        return None
    try:
        pid = uuid.UUID(value)
    except ValueError:
        raise HTTPException(422, "Bad photo id")
    if not db.get(Photo, pid):
        raise HTTPException(422, "Photo not found")
    return pid


def _ingredients(items) -> list[dict]:
    return [
        normalize_ingredient(i.model_dump(), "portion" in i.model_fields_set)
        for i in items
        if i.name.strip()
    ]


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


@router.get("/recipes")
def list_recipes(
    q: str = "",
    filter: Literal["all", "not_made", "made"] = "all",
    db: Session = Depends(get_db),
    member: str = Depends(current_member),
):
    recipes = _all_recipes(db)
    stats = {r.id: recipe_stats(r) for r in recipes}
    if q.strip():
        pairs = search_service.search(recipes, stats, q, include_names=True)
    else:
        def key(r):
            last = stats[r.id]["last_cooked"]
            return (0 if last else 1, -(last or date.min).toordinal(), -r.created_at.timestamp())

        pairs = [(r, None) for r in sorted(recipes, key=key)]
    if filter == "made":
        pairs = [p for p in pairs if stats[p[0].id]["made_count"]]
    elif filter == "not_made":
        pairs = [p for p in pairs if not stats[p[0].id]["made_count"]]
    counts = {
        "all": len(recipes),
        "made": sum(1 for r in recipes if stats[r.id]["made_count"]),
        "not_made": sum(1 for r in recipes if not stats[r.id]["made_count"]),
    }
    return {"counts": counts, "recipes": [recipe_out(r, matched=i) for r, i in pairs]}


@router.get("/search")
def search(q: str = Query(""), db: Session = Depends(get_db), member: str = Depends(current_member)):
    recipes = _all_recipes(db)
    stats = {r.id: recipe_stats(r) for r in recipes}
    pairs = search_service.search(recipes, stats, q)
    return {"query": q.strip(), "count": len(pairs), "results": [recipe_out(r, matched=i) for r, i in pairs]}


@router.post("/recipes", status_code=201)
def create_recipe(body: RecipeIn, db: Session = Depends(get_db), member: str = Depends(current_member)):
    recipe = Recipe(
        name=_clean(body.name) or "Untitled recipe",
        name_alt=_clean(body.name_alt),
        source=body.source,
        source_url=_clean(body.source_url),
        note=_clean(body.note),
        ingredients=_ingredients(body.ingredients),
        steps=[s.strip() for s in body.steps if s.strip()],
        created_by=member,
    )
    db.add(recipe)
    db.commit()
    return recipe_out(_get_recipe(db, str(recipe.id)), with_logs=True)


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str, db: Session = Depends(get_db), member: str = Depends(current_member)):
    return recipe_out(_get_recipe(db, recipe_id), with_logs=True)


@router.patch("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, body: RecipePatch, db: Session = Depends(get_db), member: str = Depends(current_member)):
    recipe = _get_recipe(db, recipe_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data:
        recipe.name = _clean(data["name"]) or "Untitled recipe"
    if "name_alt" in data:
        recipe.name_alt = _clean(data["name_alt"])
    if "note" in data:
        recipe.note = _clean(data["note"])
    if data.get("source"):
        recipe.source = data["source"]
    if "source_url" in data:
        recipe.source_url = _clean(data["source_url"])
    if "plate_id" in data:
        recipe.plate_id = data["plate_id"]
    if body.ingredients is not None:
        recipe.ingredients = _ingredients(body.ingredients)
    if body.steps is not None:
        recipe.steps = [s.strip() for s in body.steps if s.strip()]
    db.commit()
    return recipe_out(_get_recipe(db, recipe_id), with_logs=True)


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str, db: Session = Depends(get_db), member: str = Depends(current_member)):
    db.delete(_get_recipe(db, recipe_id))
    db.commit()


@router.post("/recipes/{recipe_id}/logs", status_code=201)
def create_log(recipe_id: str, body: LogIn, db: Session = Depends(get_db), member: str = Depends(current_member)):
    recipe = _get_recipe(db, recipe_id)
    log = CookLog(
        recipe_id=recipe.id,
        cooked_on=body.cooked_on or date.today(),
        rating=body.rating,
        note=_clean(body.note),
        tweaks=_clean(body.tweaks),
        photo_id=_photo_id(db, body.photo_id),
        photo_crop=body.photo_crop.model_dump() if body.photo_id and body.photo_crop else None,
        created_by=member,
    )
    db.add(log)
    db.commit()
    return log_out(log)


def _get_log(db: Session, log_id: str) -> CookLog:
    try:
        log = db.get(CookLog, uuid.UUID(log_id))
    except ValueError:
        log = None
    if not log:
        raise HTTPException(404, "Log not found")
    return log


@router.patch("/logs/{log_id}")
def update_log(log_id: str, body: LogPatch, db: Session = Depends(get_db), member: str = Depends(current_member)):
    log = _get_log(db, log_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("cooked_on"):
        log.cooked_on = data["cooked_on"]
    if "rating" in data:
        log.rating = data["rating"]
    if "note" in data:
        log.note = _clean(data["note"])
    if "tweaks" in data:
        log.tweaks = _clean(data["tweaks"])
    if data.get("photo_id"):
        log.photo_id = _photo_id(db, data["photo_id"])
    elif data.get("clear_photo"):
        log.photo_id = None
        log.photo_crop = None
    if "photo_crop" in data and log.photo_id:
        log.photo_crop = body.photo_crop.model_dump() if body.photo_crop else None
    db.commit()
    return log_out(log)


@router.delete("/logs/{log_id}", status_code=204)
def delete_log(log_id: str, db: Session = Depends(get_db), member: str = Depends(current_member)):
    db.delete(_get_log(db, log_id))
    db.commit()
