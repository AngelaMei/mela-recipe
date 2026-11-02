"""Import past recipes: POST a file with dry_run=true for a preview, then dry_run=false to save."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_member
from ..config import Settings, get_settings
from ..db import get_db
from ..models import CookLog, Photo, Recipe
from ..services.importer import MAX_RECIPES, ImportError_, ImportedRecipe, parse_upload

router = APIRouter(prefix="/api", tags=["import"])

MAX_IMPORT_BYTES = 300 * 1024 * 1024


def _key(name: str) -> str:
    return " ".join(name.lower().split())


@router.post("/import")
async def import_recipes(
    file: UploadFile = File(...),
    dry_run: bool = Form(True),
    skip_duplicates: bool = Form(True),
    db: Session = Depends(get_db),
    member: str = Depends(current_member),
    settings: Settings = Depends(get_settings),
):
    data = await file.read(MAX_IMPORT_BYTES + 1)
    if len(data) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "The file is larger than 300 MB")
    try:
        parsed = parse_upload(file.filename or "", data)
    except ImportError_ as exc:
        raise HTTPException(422, str(exc)) from exc
    if len(parsed.recipes) > MAX_RECIPES:
        raise HTTPException(422, f"The file has {len(parsed.recipes)} recipes; import at most {MAX_RECIPES} at a time")

    existing_ids = set(db.scalars(select(Recipe.id)))
    existing_names = {_key(n) for n in db.scalars(select(Recipe.name))}
    members = {m["name"] for m in settings.members}

    seen: set[str] = set()
    plan: list[tuple[ImportedRecipe, bool]] = []
    for r in parsed.recipes:
        duplicate = (r.id is not None and r.id in existing_ids) or _key(r.name) in existing_names or _key(r.name) in seen
        seen.add(_key(r.name))
        plan.append((r, duplicate))

    imported = 0
    if not dry_run:
        for r, duplicate in plan:
            if duplicate and skip_duplicates:
                continue
            _save(db, r, member, members, keep_id=r.id is not None and r.id not in existing_ids)
            imported += 1
        db.commit()

    return {
        "kind": parsed.kind,
        "dry_run": dry_run,
        "recipes": [
            {
                "name": r.name,
                "name_alt": r.name_alt,
                "ingredients": len(r.ingredients),
                "steps": len(r.steps),
                "logs": len(r.logs),
                "photos": sum(1 for l in r.logs if l.photo),
                "has_link": bool(r.source_url),
                "duplicate": duplicate,
                "warnings": r.warnings,
            }
            for r, duplicate in plan
        ],
        "warnings": parsed.warnings,
        "counts": {
            "found": len(plan),
            "new": sum(1 for _, d in plan if not d),
            "duplicates": sum(1 for _, d in plan if d),
        },
        "imported": imported,
        "total_recipes": db.scalar(select(func.count()).select_from(Recipe)),
    }


def _save(db: Session, r: ImportedRecipe, member: str, members: set[str], keep_id: bool) -> None:
    def who(name: str | None) -> str:
        return name if name in members else member

    recipe = Recipe(
        name=r.name[:200],
        name_alt=(r.name_alt or None) and r.name_alt[:200],
        source=r.source,
        source_url=r.source_url,
        note=r.note,
        ingredients=r.ingredients,
        steps=r.steps,
        plate_id=(r.plate_id or None) and r.plate_id[:32],
        created_by=who(r.created_by),
    )
    if keep_id:
        recipe.id = r.id
    if r.created_at:
        recipe.created_at = r.created_at
    db.add(recipe)
    db.flush()
    for lg in r.logs:
        photo_id = None
        if lg.photo:
            photo = Photo(content_type=lg.photo[1], data=lg.photo[0], created_by=who(lg.created_by))
            db.add(photo)
            db.flush()
            photo_id = photo.id
        log = CookLog(
            recipe_id=recipe.id,
            cooked_on=lg.cooked_on,
            rating=lg.rating,
            note=lg.note,
            tweaks=lg.tweaks,
            photo_id=photo_id,
            photo_crop=lg.photo_crop if photo_id else None,
            created_by=who(lg.created_by),
        )
        if lg.created_at:
            log.created_at = lg.created_at
        db.add(log)
