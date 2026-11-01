"""Grocery merging (addToGrocery in the design README)."""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..models import GroceryItem
from .normalize import base_unit, display_amount, key_for


def _lock_key(db: Session, key: str) -> None:
    """Serialise concurrent adds of the same ingredient from both phones."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": key})


def add_to_grocery(
    db: Session,
    *,
    name: str,
    amount: float | None,
    unit: str | None,
    by: str,
    source: str | None = None,
    recipe_id: str | None = None,
) -> GroceryItem:
    """Merge into an unchecked item with the same key and base unit, or add a row.

    Checked items never merge (they are already bought). Incompatible units
    (1 bunch + 2 stalks) stay as separate rows with the same name.
    """
    key = key_for(name) or name.strip().lower()
    base, factor = base_unit(unit)
    value = amount * factor if amount is not None else None
    entry = {"from": source, "recipe_id": recipe_id, "by": by, "amount": value}

    _lock_key(db, key)
    stmt = select(GroceryItem).where(GroceryItem.key == key, GroceryItem.checked.is_(False))
    stmt = stmt.where(GroceryItem.base_unit.is_(None) if base is None else GroceryItem.base_unit == base)
    item = db.scalars(stmt.limit(1)).first()

    if item is None:
        item = GroceryItem(name=name.strip(), key=key, base_unit=base, amount=value, sources=[entry])
        db.add(item)
    else:
        if item.amount is not None or value is not None:
            item.amount = (item.amount or 0) + (value or 0)
        item.sources = [*item.sources, entry]  # reassign so JSON change is tracked
    db.flush()
    return item


def item_out(item: GroceryItem) -> dict:
    qty, unit = display_amount(item.amount, item.base_unit)
    return {
        "id": str(item.id),
        "name": item.name,
        "key": item.key,
        "qty": qty,
        "unit": unit,
        "unitless": item.base_unit is None,
        "sources": item.sources,
        "checked": item.checked,
        "checked_at": item.checked_at.isoformat() if item.checked_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def open_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(GroceryItem).where(GroceryItem.checked.is_(False))) or 0
