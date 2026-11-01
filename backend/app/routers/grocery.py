import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import current_member
from ..db import get_db
from ..models import GroceryItem, Recipe
from ..schemas import GroceryAddIn, GroceryFromRecipeIn, GroceryPatch
from ..services.grocery import add_to_grocery, item_out
from ..services.parsing import parse_ingredient

router = APIRouter(prefix="/api/grocery", tags=["grocery"])


def _list(db: Session) -> dict:
    items = list(db.scalars(select(GroceryItem).order_by(GroceryItem.created_at)))
    open_items = [item_out(i) for i in items if not i.checked]
    basket = sorted((i for i in items if i.checked), key=lambda i: i.checked_at or i.created_at, reverse=True)
    return {"open": open_items, "basket": [item_out(i) for i in basket], "open_count": len(open_items)}


@router.get("")
def list_items(db: Session = Depends(get_db), member: str = Depends(current_member)):
    return _list(db)


@router.post("", status_code=201)
def add_item(body: GroceryAddIn, db: Session = Depends(get_db), member: str = Depends(current_member)):
    ing = parse_ingredient(body.text)  # "2 onions" -> qty 2
    if not ing.name:
        raise HTTPException(422, "Nothing to add")
    add_to_grocery(db, name=ing.name, amount=ing.amount, unit=ing.unit, by=member)
    db.commit()
    return _list(db)


@router.post("/from-recipe", status_code=201)
def add_from_recipe(body: GroceryFromRecipeIn, db: Session = Depends(get_db), member: str = Depends(current_member)):
    try:
        recipe = db.get(Recipe, uuid.UUID(body.recipe_id))
    except ValueError:
        recipe = None
    if not recipe:
        raise HTTPException(404, "Recipe not found")
    ingredients = recipe.ingredients or []
    added = 0
    for idx in sorted(set(body.indices)):
        if 0 <= idx < len(ingredients):
            ing = ingredients[idx]
            add_to_grocery(
                db, name=ing["name"], amount=ing.get("amount"), unit=ing.get("unit"),
                by=member, source=recipe.name, recipe_id=str(recipe.id),
            )
            added += 1
    db.commit()
    return {"added": added, **_list(db)}


@router.patch("/{item_id}")
def update_item(item_id: str, body: GroceryPatch, db: Session = Depends(get_db), member: str = Depends(current_member)):
    try:
        item = db.get(GroceryItem, uuid.UUID(item_id))
    except ValueError:
        item = None
    if not item:
        raise HTTPException(404, "Item not found")
    item.checked = body.checked
    item.checked_at = datetime.now(timezone.utc) if body.checked else None
    db.commit()
    return _list(db)


@router.delete("/{item_id}")
def delete_item(item_id: str, db: Session = Depends(get_db), member: str = Depends(current_member)):
    try:
        db.execute(delete(GroceryItem).where(GroceryItem.id == uuid.UUID(item_id)))
    except ValueError:
        raise HTTPException(404, "Item not found")
    db.commit()
    return _list(db)


@router.post("/clear")
def clear_basket(db: Session = Depends(get_db), member: str = Depends(current_member)):
    db.execute(delete(GroceryItem).where(GroceryItem.checked.is_(True)))
    db.commit()
    return _list(db)
