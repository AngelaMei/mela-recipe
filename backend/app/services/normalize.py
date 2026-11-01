"""Ingredient keys, aliases and units.

Shared by parsing, grocery merging and search. The rules follow the
"Interaction specs" in the design README:

- key = lower-cased name -> alias map -> simple de-pluralising
- units convert to a base unit (g, ml, tsp); other units fold plurals
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Aliases. Each group maps to its first entry (the canonical key).
# Aliases cross languages so "蔥" finds "Scallion".
# ---------------------------------------------------------------------------
ALIAS_GROUPS: list[list[str]] = [
    ["scallion", "green onion", "spring onion", "青蔥", "蔥"],
    ["eggplant", "aubergine", "茄子"],
    ["egg", "雞蛋", "蛋"],
    ["tomato", "番茄", "蕃茄"],
    ["onion", "yellow onion", "洋蔥"],
    ["garlic", "蒜", "蒜頭", "大蒜", "蒜瓣"],
    ["ginger", "薑", "老薑", "生薑"],
    ["pork", "豬肉"],
    ["ground pork", "minced pork", "豬絞肉", "絞肉"],
    ["pork belly", "五花肉"],
    ["chicken", "雞肉"],
    ["chicken thigh", "雞腿肉", "去骨雞腿"],
    ["beef", "牛肉"],
    ["tofu", "豆腐"],
    ["soy sauce", "醬油"],
    ["doubanjiang", "chili bean paste", "豆瓣醬"],
    ["cilantro", "coriander", "香菜"],
    ["basil", "九層塔", "羅勒"],
    ["rice", "白米", "米"],
    ["sugar", "糖", "砂糖"],
    ["salt", "鹽", "鹽巴"],
    ["pepper", "black pepper", "黑胡椒", "胡椒"],
    ["potato", "馬鈴薯"],
    ["carrot", "紅蘿蔔", "胡蘿蔔"],
    ["shiitake", "shiitake mushroom", "香菇"],
    ["mushroom", "蘑菇"],
    ["udon", "烏龍麵"],
    ["bell pepper", "capsicum", "甜椒", "青椒"],
    ["chili", "chilli", "chile", "辣椒"],
    ["sesame oil", "麻油", "香油"],
    ["rice wine", "米酒"],
    ["milk", "牛奶"],
    ["butter", "奶油"],
    ["flour", "麵粉"],
    ["cabbage", "高麗菜"],
    ["napa cabbage", "大白菜", "白菜"],
    ["spinach", "菠菜"],
    ["shrimp", "prawn", "蝦", "蝦仁"],
    ["lemon", "檸檬"],
    ["cumin", "孜然"],
    ["paprika", "紅椒粉"],
    ["oil", "vegetable oil", "cooking oil", "油", "沙拉油"],
    ["water", "水"],
    ["vinegar", "醋"],
    ["oyster sauce", "蠔油"],
    ["cornstarch", "corn starch", "太白粉", "玉米粉"],
    ["noodle", "麵", "麵條"],
    ["cucumber", "小黃瓜", "黃瓜"],
    ["corn", "玉米"],
    ["bean sprout", "豆芽", "豆芽菜"],
]

ALIASES: dict[str, str] = {}
ALIAS_SETS: dict[str, list[str]] = {}
for _group in ALIAS_GROUPS:
    _canon = _group[0]
    ALIAS_SETS[_canon] = _group
    for _alias in _group:
        ALIASES[_alias] = _canon

# Size / freshness words that don't change what you buy.
_STOP_WORDS = {"large", "small", "medium", "fresh", "ripe", "big"}

_CJK = re.compile(r"[㐀-鿿豈-﫿]")


def has_cjk(text: str) -> bool:
    return bool(_CJK.search(text))


def depluralise(word: str) -> str:
    if has_cjk(word) or len(word) <= 3:
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith(("ches", "shes", "sses", "xes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _clean(name: str) -> str:
    text = name.lower().strip()
    text = re.sub(r"[（(][^)）]*[)）]", " ", text)  # drop "(optional)"
    text = re.sub(r"[^\w\s&'-]", " ", text)
    words = [w for w in text.split() if w not in _STOP_WORDS]
    return " ".join(words)


def key_for(name: str) -> str:
    """Grocery / search key for an ingredient name."""
    text = _clean(name)
    if not text:
        return ""
    if text in ALIASES:
        return ALIASES[text]
    words = text.split()
    words[-1] = depluralise(words[-1])
    singular = " ".join(words)
    return ALIASES.get(singular, singular)


def aliases_for(key: str) -> list[str]:
    return ALIAS_SETS.get(key, [key])


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
# written form -> (base unit, factor)
_CONVERT: dict[str, tuple[str, float]] = {
    "g": ("g", 1), "gram": ("g", 1), "grams": ("g", 1), "gr": ("g", 1),
    "克": ("g", 1), "公克": ("g", 1),
    "kg": ("g", 1000), "kilogram": ("g", 1000), "kilograms": ("g", 1000),
    "公斤": ("g", 1000), "斤": ("g", 600),
    "ml": ("ml", 1), "milliliter": ("ml", 1), "milliliters": ("ml", 1),
    "millilitre": ("ml", 1), "millilitres": ("ml", 1), "毫升": ("ml", 1), "cc": ("ml", 1),
    "l": ("ml", 1000), "liter": ("ml", 1000), "liters": ("ml", 1000),
    "litre": ("ml", 1000), "litres": ("ml", 1000), "公升": ("ml", 1000),
    "tsp": ("tsp", 1), "teaspoon": ("tsp", 1), "teaspoons": ("tsp", 1),
    "小匙": ("tsp", 1), "茶匙": ("tsp", 1),
    "tbsp": ("tsp", 3), "tbs": ("tsp", 3), "tablespoon": ("tsp", 3),
    "tablespoons": ("tsp", 3), "大匙": ("tsp", 3), "湯匙": ("tsp", 3),
}

# Plural -> singular for units that don't convert.
_FOLD: dict[str, str] = {
    "cups": "cup", "cloves": "clove", "bunches": "bunch", "stalks": "stalk",
    "sprigs": "sprig", "pieces": "piece", "pcs": "piece", "pc": "piece",
    "cans": "can", "slices": "slice", "pinches": "pinch", "handfuls": "handful",
    "heads": "head", "sticks": "stick", "packs": "pack", "packets": "packet",
    "jars": "jar", "lbs": "lb", "pounds": "lb", "pound": "lb",
    "ounces": "oz", "ounce": "oz", "leaves": "leaf",
}

EN_UNITS = sorted(
    {u for u in list(_CONVERT) + list(_FOLD) + list(_FOLD.values()) if not has_cjk(u)},
    key=len,
    reverse=True,
)
ZH_UNITS = sorted(
    [u for u in _CONVERT if has_cjk(u)]
    + ["杯", "瓣", "根", "顆", "個", "片", "把", "支", "條", "塊", "包", "罐",
       "碗", "匙", "隻", "粒", "尾", "盒", "張", "撮", "滴", "朵", "株", "球", "份"],
    key=len,
    reverse=True,
)


def base_unit(unit: str | None) -> tuple[str | None, float]:
    """Return (base unit, factor). Unitless -> (None, 1)."""
    if not unit:
        return None, 1
    u = unit.strip().lower()
    if u in _CONVERT:
        return _CONVERT[u]
    return _FOLD.get(u, u), 1


def format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def display_amount(amount: float | None, base: str | None) -> tuple[str | None, str | None]:
    """1000 g -> ("1", "kg"); 6 tsp -> ("2", "tbsp")."""
    if amount is None:
        return None, base
    if base == "g" and amount >= 1000:
        return format_number(amount / 1000), "kg"
    if base == "ml" and amount >= 1000:
        return format_number(amount / 1000), "l"
    if base == "tsp" and amount >= 3 and abs(amount / 3 - round(amount / 3)) < 1e-9:
        return format_number(amount / 3), "tbsp"
    return format_number(amount), base
