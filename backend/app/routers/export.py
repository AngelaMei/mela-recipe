"""Backup: download everything as one .zip.

    mela-backup-2026-11-02.zip
    ├── mela-backup.json   every recipe, cook log and grocery item (machine-readable, for restoring)
    ├── recipes.md         all recipes as readable text
    └── photos/<id>.jpg    every cook-log photo
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import current_member
from ..config import Settings, get_settings
from ..db import get_db
from ..models import GroceryItem, Photo, Recipe
from ..serialize import recipe_stats
from ..services.lines import portion_text

router = APIRouter(prefix="/api", tags=["export"])

FORMAT_VERSION = 1
_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic", "image/heif": "heif"}


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, (date, datetime)) else None


def _portion(ing: dict) -> str | None:
    return ing["portion"] if "portion" in ing else portion_text(ing.get("qty"), ing.get("unit"), ing.get("note"))


def _markdown(recipes: list[Recipe], household: str, exported_at: datetime) -> str:
    out = [f"# {household}: recipes", "", f"Exported {exported_at:%Y-%m-%d %H:%M} UTC · {len(recipes)} recipes", ""]
    for r in recipes:
        stats = recipe_stats(r)
        out += ["---", "", f"## {r.name}"]
        if r.name_alt:
            out.append(f"*{r.name_alt}*")
        meta = [f"Made {stats['made_count']}×" if stats["made_count"] else "Not made yet"]
        if stats["avg_rating"]:
            meta.append(f"★ {stats['avg_rating']}")
        if r.source_url:
            meta.append(r.source_url)
        out += ["", " · ".join(meta), ""]
        if r.plate_id:
            out += [f"Plate: {r.plate_id}", ""]
        if r.note:
            out += [f"> {line}" for line in r.note.split("\n")] + [""]
        if r.ingredients:
            out.append("### Ingredients")
            for ing in r.ingredients:
                portion = _portion(ing)
                out.append(f"- {ing['name']}" + (f" — {portion}" if portion else ""))
            out.append("")
        if r.steps:
            out.append("### Steps")
            out += [f"{i}. {s}" for i, s in enumerate(r.steps, 1)]
            out.append("")
        if r.logs:
            out.append("### Cook log")
            for log in r.logs:
                line = f"- {log.cooked_on.isoformat()}"
                if log.rating:
                    line += " " + "★" * log.rating
                line += f" ({log.created_by})"
                if log.note:
                    line += f": {log.note}"
                if log.tweaks:
                    line += f" Tweaks: {log.tweaks}"
                out.append(line)
            out.append("")
    return "\n".join(out)


@router.get("/export")
def export_backup(
    db: Session = Depends(get_db),
    member: str = Depends(current_member),
    settings: Settings = Depends(get_settings),
):
    now = datetime.now(timezone.utc)
    recipes = list(
        db.scalars(select(Recipe).options(selectinload(Recipe.logs)).order_by(Recipe.created_at))
    )
    photo_types = dict(db.execute(select(Photo.id, Photo.content_type)).all())

    def photo_path(pid) -> str | None:
        if not pid or pid not in photo_types:
            return None
        return f"photos/{pid}.{_EXT.get(photo_types[pid], 'jpg')}"

    data = {
        "format": "mela-backup",
        "version": FORMAT_VERSION,
        "exported_at": now.isoformat(),
        "exported_by": member,
        "household": {"name": settings.mela_household, "members": settings.members},
        "recipes": [
            {
                "id": str(r.id),
                "name": r.name,
                "name_alt": r.name_alt,
                "source": r.source,
                "source_url": r.source_url,
                "note": r.note,
                "ingredients": [{**i, "portion": _portion(i)} for i in (r.ingredients or [])],
                "steps": r.steps or [],
                "plate_id": r.plate_id,
                "created_by": r.created_by,
                "created_at": _iso(r.created_at),
                "updated_at": _iso(r.updated_at),
                "logs": [
                    {
                        "id": str(l.id),
                        "cooked_on": l.cooked_on.isoformat(),
                        "rating": l.rating,
                        "note": l.note,
                        "tweaks": l.tweaks,
                        "photo": photo_path(l.photo_id),
                        "photo_crop": l.photo_crop,
                        "created_by": l.created_by,
                        "created_at": _iso(l.created_at),
                    }
                    for l in sorted(r.logs, key=lambda l: (l.cooked_on, l.created_at))
                ],
            }
            for r in recipes
        ],
        "grocery": [
            {
                "name": g.name,
                "key": g.key,
                "amount": g.amount,
                "base_unit": g.base_unit,
                "sources": g.sources,
                "checked": g.checked,
                "created_at": _iso(g.created_at),
            }
            for g in db.scalars(select(GroceryItem).order_by(GroceryItem.created_at))
        ],
    }

    # Photos can add up, so build the zip on disk past a few MB rather than in memory.
    buf = tempfile.SpooledTemporaryFile(max_size=16 * 1024 * 1024)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mela-backup.json", json.dumps(data, ensure_ascii=False, indent=2))
        zf.writestr("recipes.md", _markdown(recipes, settings.mela_household, now))
        used = {l.photo_id for r in recipes for l in r.logs if l.photo_id}
        for pid in used:
            path = photo_path(pid)
            photo = db.get(Photo, pid)
            if path and photo:
                # JPEG/PNG/WebP are already compressed
                zf.writestr(path, photo.data, compress_type=zipfile.ZIP_STORED)
                db.expunge(photo)  # don't keep every photo's bytes in the session
    buf.seek(0)

    def chunks():
        try:
            while block := buf.read(256 * 1024):
                yield block
        finally:
            buf.close()

    filename = f"mela-backup-{now:%Y-%m-%d}.zip"
    return StreamingResponse(
        chunks(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )
