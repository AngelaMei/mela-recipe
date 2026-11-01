"""Rule-based recipe parsing (no AI).

Implements "Interaction specs" from the design README:
detect_source, parse_recipe, parse_ingredient and split_steps.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .normalize import EN_UNITS, ZH_UNITS, has_cjk

# ---------------------------------------------------------------------------
# Source detection
# ---------------------------------------------------------------------------
_URL = re.compile(r"^(?:https?://)?(?:[\w-]+\.)+[a-z]{2,}(?:[/?#]\S*)?$", re.I)


def detect_source(text: str) -> str:
    """youtube | instagram | link | text"""
    stripped = text.strip()
    if stripped and len(stripped.split()) == 1:
        low = stripped.lower()
        if "youtu.be" in low or "youtube.com" in low:
            return "youtube"
        if "instagram.com" in low:
            return "instagram"
        if _URL.match(stripped):
            return "link"
    return "text"


# ---------------------------------------------------------------------------
# Quantities and units
# ---------------------------------------------------------------------------
_FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3,
              "⅛": 0.125, "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}
_ZH_NUM = {"一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6,
           "七": 7, "八": 8, "九": 9, "十": 10, "半": 0.5}

_FR = "".join(_FRACTIONS)
_ASCII_NUM = rf"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?\s?[{_FR}]?|[{_FR}])"
_ZH_NUM_RE = r"[一二兩三四五六七八九十半]"
_RANGE = r"(?:\s*(?:-|–|~|～|to)\s*)"
ASCII_QTY = rf"{_ASCII_NUM}(?:{_RANGE}{_ASCII_NUM})?"
ZH_QTY = rf"{_ZH_NUM_RE}(?:{_RANGE}?{_ZH_NUM_RE})?"

_EN_UNIT = r"(?:" + "|".join(re.escape(u) for u in EN_UNITS) + r")\.?(?![A-Za-z])"
_ZH_UNIT = r"(?:" + "|".join(re.escape(u) for u in ZH_UNITS) + r")"
UNIT = rf"(?:{_EN_UNIT}|{_ZH_UNIT})"

# Words after a number that mean it's a time or temperature, not an amount.
_NOT_AMOUNT = re.compile(
    r"^\s*(?:min|mins|minute|minutes|sec|secs|second|seconds|hr|hrs|hour|hours|"
    r"°|degrees?|f\b|c\b|分鐘|分|秒|小時|度)",
    re.I,
)
_TO_TASTE = re.compile(r"\s*(適量|少許|酌量|to taste|as needed|optional)\s*$", re.I)
_STEP_NUMBER = re.compile(r"^\s*(?:step\s*)?\d{1,2}\s*[.)、:：](?!\d)", re.I)

# "qty unit name" and "name qty unit"
_QTY_FIRST = re.compile(
    rf"^(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?\s*(?:of\s+)?(?P<name>.*)$", re.I
)
_QTY_LAST = re.compile(
    rf"^(?P<name>.+?)\s*[:：]?\s*(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?$", re.I
)
_PREP_WORDS = re.compile(
    r"^(?:finely\s+|roughly\s+|thinly\s+)?(?:chopped|diced|minced|sliced|beaten|grated|"
    r"peeled|crushed|cubed|julienned|softened|melted|divided|optional|to serve|"
    r"切丁|切碎|切片|切絲|切段|切塊|拍碎|打散|磨泥)$",
    re.I,
)


def _num(token: str) -> float:
    token = token.strip()
    if token in _ZH_NUM:
        return _ZH_NUM[token]
    if len(token) == 2 and all(c in _ZH_NUM for c in token):
        # 十二 style, kept simple: "十" + digit
        if token[0] == "十":
            return 10 + _ZH_NUM[token[1]]
        return _ZH_NUM[token[0]]  # 一二 → treat as range start
    m = re.match(r"^(\d+)\s+(\d+)/(\d+)$", token)
    if m:
        return int(m[1]) + int(m[2]) / int(m[3])
    m = re.match(r"^(\d+)/(\d+)$", token)
    if m:
        return int(m[1]) / int(m[2]) if int(m[2]) else 0
    m = re.match(rf"^(\d+(?:\.\d+)?)?\s?([{_FR}])?$", token)
    if m and (m[1] or m[2]):
        return (float(m[1]) if m[1] else 0) + (_FRACTIONS[m[2]] if m[2] else 0)
    return float(token)


def parse_qty(text: str) -> float | None:
    """'1 1/2' -> 1.5, '2-3' -> 2 (the low end of a range), '半' -> 0.5."""
    first = re.split(_RANGE, text.strip(), maxsplit=1)[0]
    try:
        return _num(first)
    except (ValueError, KeyError):
        return None


@dataclass
class Ingredient:
    name: str
    amount: float | None = None   # numeric quantity, for merging
    qty: str | None = None        # quantity as written, for display
    unit: str | None = None       # unit as written ("cloves", "瓣")
    note: str | None = None       # 適量, "to taste", "chopped"

    def to_dict(self) -> dict:
        return asdict(self)


def _is_zh_qty(qty: str) -> bool:
    return bool(re.match(_ZH_NUM_RE, qty.strip()))


def _clean_unit(unit: str | None) -> str | None:
    return unit.strip().rstrip(".") if unit else None


def parse_ingredient(text: str) -> Ingredient:
    """Parse one ingredient ('2 cloves garlic', '蒜頭 3瓣', '鹽 適量')."""
    line = _strip_bullet(text).strip()
    note = None
    m = _TO_TASTE.search(line)
    if m and m.start() > 0:
        note = m[1]
        line = line[: m.start()].strip()

    m = _QTY_FIRST.match(line)
    if m and m["name"].strip() and not _NOT_AMOUNT.match(line[m.end("qty"):]):
        # Chinese numerals only count with a unit (二砂糖 is a sugar, not 2 sugar).
        if not _is_zh_qty(m["qty"]) or m["unit"]:
            name = m["name"].strip(" ,，:：")
            return Ingredient(name=name, amount=parse_qty(m["qty"]),
                              qty=m["qty"].strip(), unit=_clean_unit(m["unit"]), note=note)

    m = _QTY_LAST.match(line)
    if m and (not _is_zh_qty(m["qty"]) or m["unit"]):
        name = m["name"].strip(" ,，:：")
        # "egg 2" yes; "step 2" / "cook 10" without a unit only when short
        if name and (m["unit"] or len(name) <= 20):
            return Ingredient(name=name, amount=parse_qty(m["qty"]),
                              qty=m["qty"].strip(), unit=_clean_unit(m["unit"]), note=note)

    return Ingredient(name=line.strip(" ,，:："), note=note)


def parse_ingredient_line(line: str) -> list[Ingredient]:
    """Split on , ， 、 and parse each piece. Prep words attach to the previous item."""
    items: list[Ingredient] = []
    for piece in re.split(r"[,，、]", line):
        piece = piece.strip()
        if not piece:
            continue
        if items and _PREP_WORDS.match(piece):
            prev = items[-1]
            prev.note = f"{prev.note}, {piece}" if prev.note else piece
            continue
        ing = parse_ingredient(piece)
        if ing.name:
            items.append(ing)
    return items


def looks_like_ingredient(line: str) -> bool:
    """Heuristic for text without section headers."""
    text = _strip_bullet(line).strip()
    if not text or len(text) > 40 or _STEP_NUMBER.match(text):
        return False
    if _TO_TASTE.search(text) and _TO_TASTE.search(text).start() > 0:
        return True
    m = re.match(rf"^(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?", text, re.I)
    if m:
        rest = text[m.end("qty"):]
        if _NOT_AMOUNT.match(rest):
            return False
        if _is_zh_qty(m["qty"]):
            return bool(m["unit"])
        return bool(m["unit"]) or bool(re.match(r"^\s+\S", rest)) or bool(re.match(r"^[^\W\d_]", rest))
    m = re.search(rf"(?:{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})$", text, re.I)
    return bool(m)


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------
_BULLET = re.compile(r"^\s*[-–—•*·▪◦●○→>✓✔️]+\s*")
_LEAD_NUMBER = re.compile(r"^\s*(?:step\s*)?\d{1,2}\s*[.)、:：](?!\d)\s*", re.I)
_NUMBER_SPLIT = re.compile(r"(?:^|(?<=\s)|(?<=[。.!！?？]))(?:step\s*)?\d{1,2}\s*[.)、:：](?!\d)\s*", re.I | re.M)


def _strip_bullet(text: str) -> str:
    return _BULLET.sub("", text)


@dataclass
class SplitOptions:
    line: bool = True
    comma: bool = True
    number: bool = True
    period: bool = False


def _join(a: str, b: str) -> str:
    if not a:
        return b
    sep = "" if has_cjk(a[-1]) or has_cjk(b[:1]) else " "
    return f"{a}{sep}{b}"


def split_steps(text: str, opts: SplitOptions | None = None) -> list[dict]:
    opts = opts or SplitOptions()
    pieces = [text.replace("\r\n", "\n").replace("\r", "\n")]

    if opts.number:
        pieces = [p for chunk in pieces for p in _NUMBER_SPLIT.split(chunk)]
    if opts.line:
        pieces = [p for chunk in pieces for p in chunk.split("\n")]
    else:
        joined = []
        for chunk in pieces:
            acc = ""
            for ln in chunk.split("\n"):
                acc = _join(acc, ln.strip())
            joined.append(acc)
        pieces = joined
    if opts.comma:
        pieces = [p for chunk in pieces for p in re.split(r"[,，、;；]", chunk)]
    if opts.period:
        pieces = [p for chunk in pieces for p in re.split(r"。|\.\s+|\.$", chunk)]

    cleaned: list[str] = []
    for p in pieces:
        p = _LEAD_NUMBER.sub("", _strip_bullet(p)).strip()
        p = p.strip(" ,，;；")
        if not p:
            continue
        if len(p) < 3 and cleaned:
            cleaned[-1] = _join(cleaned[-1], p)
        else:
            cleaned.append(p)
    return [{"text": s, "short": len(s) < 8} for s in cleaned]


# ---------------------------------------------------------------------------
# Whole recipe
# ---------------------------------------------------------------------------
_HEADER_TAIL = r"\s*(?:[（(][^)）]*[)）])?\s*[】\]]?\s*[:：]?"
_ING_HEADER = re.compile(
    rf"^\s*(?:#+\s*)?[【\[]?\s*(?:ingredients?|食材|材料|準備材料|材料準備){_HEADER_TAIL}\s*(?P<rest>.*)$", re.I
)
_STEP_HEADER = re.compile(
    rf"^\s*(?:#+\s*)?[【\[]?\s*(?:steps?|method|directions|instructions|how to make|作法|做法|步驟|料理步驟){_HEADER_TAIL}\s*(?P<rest>.*)$",
    re.I,
)
_JUNK_LINE = re.compile(r"^\s*(?:\d{1,2}:\d{2}(?::\d{2})?\b.*|[-=_*~·•]{3,})\s*$")
_JUNK_TOKEN = re.compile(r"^(?:https?://\S+|www\.\S+|#\S+|@\S+)$", re.I)


def _is_junk(line: str) -> bool:
    """Timestamps, separators, and lines made only of links / hashtags / handles."""
    if _JUNK_LINE.match(line):
        return True
    tokens = line.split()
    return bool(tokens) and all(_JUNK_TOKEN.match(t) for t in tokens)


def _header(line: str) -> tuple[str | None, str]:
    # Only treat as a header when the keyword is the whole line or followed by ':'
    for kind, rx in (("ingredients", _ING_HEADER), ("steps", _STEP_HEADER)):
        m = rx.match(line)
        if m:
            rest = m["rest"].strip()
            if not rest or re.search(r"[:：]", line[: m.start("rest")]):
                return kind, rest
    return None, ""


@dataclass
class ParsedRecipe:
    ingredients: list[Ingredient] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)
    has_headers: bool = False

    def to_dict(self) -> dict:
        return {
            "ingredients": [i.to_dict() for i in self.ingredients],
            "steps": self.steps,
            "has_headers": self.has_headers,
        }


def parse_recipe(text: str, opts: SplitOptions | None = None) -> ParsedRecipe:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    has_headers = any(_header(ln)[0] for ln in lines)
    has_step_header = any(_header(ln)[0] == "steps" for ln in lines)

    ing_lines: list[str] = []
    step_lines: list[str] = []

    if has_headers:
        section: str | None = None
        for raw in lines:
            kind, rest = _header(raw)
            if kind:
                section = kind
                if rest:
                    (ing_lines if kind == "ingredients" else step_lines).append(rest)
                continue
            line = raw.strip()
            if not line or _is_junk(line) or section is None:
                continue  # text before the first header is the intro / title
            if section == "ingredients":
                if re.search(r"[:：]$", line) and len(line) <= 30:
                    continue  # sub-heading like "For the sauce:"
                if not has_step_header and len(line) > 40 and not looks_like_ingredient(line):
                    step_lines.append(line)
                else:
                    ing_lines.append(line)
            else:
                step_lines.append(line)
    else:
        for raw in lines:
            line = raw.strip()
            if not line or _is_junk(line):
                continue
            (ing_lines if looks_like_ingredient(line) else step_lines).append(line)

    ingredients = [ing for ln in ing_lines for ing in parse_ingredient_line(ln)]
    steps = split_steps("\n".join(step_lines), opts) if step_lines else []
    return ParsedRecipe(ingredients=ingredients, steps=steps, has_headers=has_headers)
