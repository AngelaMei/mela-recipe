"""Ingredient search (searchRecipes in the design README)."""

from __future__ import annotations

import re
from datetime import date

from .normalize import aliases_for, has_cjk, key_for


def _contains(haystack: str, needle: str, whole_word: bool) -> bool:
    haystack, needle = haystack.lower(), needle.lower().strip()
    if not needle:
        return False
    if has_cjk(needle):
        return needle in haystack
    if whole_word:
        # "egg" matches "eggs" and "beaten egg", not "eggplant"
        return re.search(rf"(?<![a-z]){re.escape(needle)}(?:s|es)?(?![a-z])", haystack) is not None
    return re.search(rf"(?<![a-z]){re.escape(needle)}", haystack) is not None


def match_ingredient(ingredients: list[dict], query: str, whole_word: bool = True) -> int | None:
    """Index of the first ingredient that matches the query, or None."""
    qkey = key_for(query)
    aliases = aliases_for(qkey) if qkey else []
    for i, ing in enumerate(ingredients):
        name = ing.get("name") or ""
        if qkey and key_for(name) == qkey:
            return i
        if _contains(name, query, whole_word):
            return i
        # cross-language: "茄子" finds "Chinese eggplant"
        if any(_contains(name, a, True) for a in aliases if a != query):
            return i
    return None


def _sort_key(item: tuple) -> tuple:
    _recipe, _idx, last_cooked, created_at = item
    # cooked first (latest first), then not-made by newest saved
    return (0 if last_cooked else 1, -(last_cooked or date.min).toordinal(), -created_at.timestamp())


def search(recipes: list, stats: dict, query: str, include_names: bool = False) -> list[tuple]:
    """Return [(recipe, matched_ingredient_index | None)] sorted per the spec.

    Every recipe that uses the ingredient, made and not made alike. If nothing
    matches as a whole word, fall back to prefix matching so partial typing works.
    """
    query = query.strip()
    if not query:
        return []

    def run(whole_word: bool) -> list[tuple]:
        hits = []
        for r in recipes:
            idx = match_ingredient(r.ingredients or [], query, whole_word)
            name_hit = include_names and (
                _contains(r.name, query, False) or (r.name_alt and _contains(r.name_alt, query, False))
            )
            if idx is not None or name_hit:
                s = stats.get(r.id, {})
                hits.append((r, idx, s.get("last_cooked"), r.created_at))
        return hits

    hits = run(True) or run(False)
    hits.sort(key=_sort_key)
    return [(r, idx) for r, idx, _, _ in hits]
