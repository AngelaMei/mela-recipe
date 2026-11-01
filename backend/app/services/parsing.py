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


_TRAILING_PAREN = re.compile(r"\s*[（(]([^()（）]*)[)）]\s*$")
_MULTIPLIER = re.compile(r"^(\d+(?:\.\d+)?)\s*[x×]\s+", re.I)


def _core(text: str) -> tuple[str, str | None]:
    """Strip bullets, a trailing '(diced)' / '（切末）' note and a '2x' multiplier."""
    line = _strip_bullet(text).strip()
    note = None
    m = _TRAILING_PAREN.search(line)
    if m and m.start() > 0:
        note = m[1].strip() or None
        line = line[: m.start()].strip()
    line = _MULTIPLIER.sub(r"\1 ", line)
    return line, note


def _add_note(a: str | None, b: str | None) -> str | None:
    return ", ".join(x for x in (a, b) if x) or None


def parse_ingredient(text: str) -> Ingredient:
    """Parse one ingredient ('2 cloves garlic', '蒜頭 3瓣', '鹽 適量')."""
    line, note = _core(text)
    m = _TO_TASTE.search(line)
    if m and m.start() > 0:
        note = _add_note(m[1], note)
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


def _split_outside_parens(line: str) -> list[str]:
    """Split on , ， 、 but not inside (…) / （…）: '蒜 3瓣（切末，拍碎）' stays whole."""
    pieces, buf, depth = [], "", 0
    for ch in line:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth = max(0, depth - 1)
        if ch in ",，、" and depth == 0:
            pieces.append(buf)
            buf = ""
        else:
            buf += ch
    pieces.append(buf)
    return pieces


def parse_ingredient_line(line: str) -> list[Ingredient]:
    """Split on , ， 、 and parse each piece. Prep words attach to the previous item."""
    items: list[Ingredient] = []
    for piece in _split_outside_parens(line):
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
    if _STEP_NUMBER.match(line):
        return False
    text, _ = _core(line)
    if not text or len(text) > 40:
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
    if m:
        return True
    # "Eggs 2": a short name and a bare number
    m = re.match(rf"^(?P<name>[^\d]{{1,20}}?)\s*[:：]?\s+(?P<qty>{ASCII_QTY})$", text, re.I)
    if m and not _starts_with_verb(m["name"]) and not _NOT_AMOUNT.match(text[m.end("qty"):]):
        return True
    return _is_item_list(text)


# Lines that start with these are instructions, not items.
_EN_VERBS = {
    "add", "bake", "beat", "blanch", "boil", "bring", "chop", "combine", "cook", "cool", "cover", "cut",
    "dice", "drain", "fold", "fry", "garnish", "grill", "heat", "let", "marinate", "melt", "mince", "mix",
    "peel", "place", "pour", "preheat", "put", "reduce", "remove", "rinse", "roast", "saute", "sauté",
    "season", "serve", "set", "simmer", "slice", "soak", "sprinkle", "steam", "stir", "strain", "taste",
    "toss", "top", "transfer", "turn", "wash", "whisk", "enjoy", "then", "and", "until", "once",
    "scramble", "knead", "rest", "roll", "spread", "brush", "flip", "wait", "keep", "make", "use",
    "squeeze", "shred", "crack", "break", "blend", "puree", "chill", "freeze", "store", "divide",
}
# Sentence words: a line with these reads as an instruction ("fry the eggs").
_EN_SENTENCE = {"the", "a", "an", "into", "with", "until", "in", "on", "onto", "for", "it", "them", "is", "are"}
# Cooking-verb characters anywhere in a short Chinese line ("番茄切塊", "雞蛋打散").
_ZH_VERB_ANY = re.compile(r"[切炒煮拌蒸煎炸燙汆洗醃撒攪放加倒打泡烤淋燜滷翻剁剝削燉焯滾熬]")
_ZH_VERB_START = re.compile(r"^(?:切|炒|加|煮|放|倒|拌|蒸|煎|炸|燙|汆|洗|醃|撒|攪|下|起|熱|先|再|然|把|將|用|等|待|最後|接著|轉|關|蓋|燜|滷|烤|淋|擺|盛|泡|沖|翻)")


def _starts_with_verb(text: str) -> bool:
    text = text.strip().lower()
    if not text:
        return False
    if has_cjk(text[:1]):
        return bool(_ZH_VERB_START.match(text))
    return text.split()[0].strip(",.:;") in _EN_VERBS


def _is_bare_item(text: str) -> bool:
    """A short noun-ish line such as 'salt' or '蔥花': no verb, no sentence punctuation."""
    core, _ = _core(text)
    if not core or _STEP_NUMBER.match(text) or re.search(r"[。.!！?？;；]", core):
        return False
    if has_cjk(core):
        if len(core) > 8 or _ZH_VERB_ANY.search(core):
            return False
    else:
        words = [w.strip(",.:;").lower() for w in core.split()]
        if len(core) > 24 or len(words) > 3 or any(w in _EN_SENTENCE for w in words):
            return False
    return not _starts_with_verb(core)


def _is_item_list(text: str) -> bool:
    """'雞蛋、番茄、蔥' / 'eggs, tomatoes, scallions': two or more bare items."""
    pieces = [p.strip() for p in _split_outside_parens(text) if p.strip()]
    return len(pieces) >= 2 and all(_is_bare_item(p) for p in pieces)


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
        kept = [ln.strip() for ln in lines if ln.strip() and not _is_junk(ln.strip())]
        is_ing = [looks_like_ingredient(ln) for ln in kept]
        bare = [_is_bare_item(ln) for ln in kept]
        # Bare items ("salt", "蔥花") count as ingredients when they sit next to
        # ingredients, or in a run of two or more at the top, before the steps.
        changed = True
        while changed:
            changed = False
            for i, ln in enumerate(kept):
                if is_ing[i] or not bare[i]:
                    continue
                near = (i > 0 and is_ing[i - 1]) or (i + 1 < len(kept) and is_ing[i + 1])
                if near:
                    is_ing[i] = changed = True
        if not any(is_ing):
            run = 0
            while run < len(kept) and bare[run]:
                run += 1
            if run >= 2 and run < len(kept):
                for i in range(run):
                    is_ing[i] = True
        for ln, ing in zip(kept, is_ing):
            (ing_lines if ing else step_lines).append(ln)

    ingredients = [ing for ln in ing_lines for ing in parse_ingredient_line(ln)]
    steps = split_steps("\n".join(step_lines), opts) if step_lines else []
    return ParsedRecipe(ingredients=ingredients, steps=steps, has_headers=has_headers)
