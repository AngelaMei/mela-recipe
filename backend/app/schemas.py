from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    amount: float | None = None
    qty: str | None = Field(default=None, max_length=40)
    unit: str | None = Field(default=None, max_length=32)
    note: str | None = Field(default=None, max_length=200)


class SplitIn(BaseModel):
    line: bool = True
    comma: bool = True
    number: bool = True
    period: bool = False


class ParseIn(BaseModel):
    input: str = Field(default="", max_length=50_000)
    caption: str | None = Field(default=None, max_length=50_000)
    split: SplitIn = SplitIn()


class RecipeIn(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    name_alt: str | None = Field(default=None, max_length=200)
    source: Literal["youtube", "instagram", "link", "manual"] = "manual"
    source_url: str | None = Field(default=None, max_length=2000)
    note: str | None = Field(default=None, max_length=2000)
    ingredients: list[IngredientIn] = []
    steps: list[str] = []


class RecipePatch(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    name_alt: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=2000)
    plate_id: str | None = Field(default=None, max_length=32)
    ingredients: list[IngredientIn] | None = None
    steps: list[str] | None = None


class LogIn(BaseModel):
    cooked_on: date | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    note: str | None = Field(default=None, max_length=4000)
    tweaks: str | None = Field(default=None, max_length=4000)
    photo_id: str | None = None


class LogPatch(LogIn):
    clear_photo: bool = False


class LoginIn(BaseModel):
    member: str
    passcode: str


class GroceryAddIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class GroceryFromRecipeIn(BaseModel):
    recipe_id: str
    indices: list[int]


class GroceryPatch(BaseModel):
    checked: bool
