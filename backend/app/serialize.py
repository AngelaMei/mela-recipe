"""Turn ORM rows into the JSON the web app reads."""

from __future__ import annotations

from datetime import date

from .models import CookLog, Recipe
from .services.lines import portion_text


def photo_url(photo_id) -> str | None:
    return f"/api/photos/{photo_id}" if photo_id else None


def recipe_stats(recipe: Recipe) -> dict:
    logs = recipe.logs
    ratings = [l.rating for l in logs if l.rating]
    last: date | None = max((l.cooked_on for l in logs), default=None)
    with_photo = next((l for l in logs if l.photo_id), None)  # logs are newest first
    return {
        "made_count": len(logs),
        "last_cooked": last,
        "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "photo_url": photo_url(with_photo.photo_id) if with_photo else None,
        "photo_crop": with_photo.photo_crop if with_photo else None,
    }


def log_out(log: CookLog) -> dict:
    return {
        "id": str(log.id),
        "recipe_id": str(log.recipe_id),
        "cooked_on": log.cooked_on.isoformat(),
        "rating": log.rating,
        "note": log.note,
        "tweaks": log.tweaks,
        "photo_url": photo_url(log.photo_id),
        "photo_id": str(log.photo_id) if log.photo_id else None,
        "photo_crop": log.photo_crop,
        "created_by": log.created_by,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def recipe_out(recipe: Recipe, *, with_logs: bool = False, matched: int | None = None) -> dict:
    stats = recipe_stats(recipe)
    out = {
        "id": str(recipe.id),
        "name": recipe.name,
        "name_alt": recipe.name_alt,
        "source": recipe.source,
        "source_url": recipe.source_url,
        "note": recipe.note,
        "ingredients": [
            i if "portion" in i else {**i, "portion": portion_text(i.get("qty"), i.get("unit"), i.get("note"))}
            for i in (recipe.ingredients or [])
        ],
        "steps": recipe.steps or [],
        "plate_id": recipe.plate_id,
        "created_by": recipe.created_by,
        "created_at": recipe.created_at.isoformat() if recipe.created_at else None,
        "made_count": stats["made_count"],
        "last_cooked": stats["last_cooked"].isoformat() if stats["last_cooked"] else None,
        "avg_rating": stats["avg_rating"],
        "photo_url": stats["photo_url"],
        "photo_crop": stats["photo_crop"],
    }
    if with_logs:
        out["logs"] = [log_out(l) for l in recipe.logs]
    if matched is not None:
        out["matched_index"] = matched
    return out
