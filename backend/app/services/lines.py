"""Structured recipe input: one ingredient per line, one step per line.

The person already says which lines are ingredients and which are steps, so
nothing here guesses that. For an ingredient line the only job is to split it
into a name and an amount ("portion"), keeping the amount exactly as typed:

    雞腿 300g            -> 雞腿 | 300g
    大蒜 1瓣（拍碎）      -> 大蒜 | 1瓣（拍碎）
    鹽 少許              -> 鹽   | 少許
    2 cloves garlic      -> garlic | 2 cloves
    Olive oil: 2 tbsp    -> Olive oil | 2 tbsp
    香菜                 -> 香菜 | (no amount)

The portion is then read for a number and unit (parse_portion) so the grocery
list can merge amounts; what's shown to people is always the portion as typed.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .normalize import base_unit
from .parsing import ASCII_QTY, UNIT, ZH_QTY, _is_zh_qty, parse_qty

_TASTE_WORDS = r"(?:適量|少許|酌量|少量|一點點|to taste|as needed|optional|a pinch|pinch)"
_PAREN = r"(?:\s*[（(][^()（）]*[)）])?"
_ABOUT = r"(?:約|大約|about|approx\.?|~)?\s*"
_AMOUNT = rf"(?:{ASCII_QTY}|{ZH_QTY})\s*(?:{UNIT})?"
# "1大匙 + 1小匙"
_MORE = rf"(?:\s*[+＋]\s*{_AMOUNT})*"
# "2 顆，切塊" / "1 onion, diced": a short prep note after the amount
_PREP = r"(?:\s*[,，]\s*[^,，\d]{1,12})?"

# Amount at the end: "雞腿 300g", "雞腿300g", "Eggs 2", "鹽 少許", "蔥 2根（切段）", "olive oil, 2 tbsp"
_PORTION_END = re.compile(
    rf"^(?P<name>.*?[^\s:：,，\-–—…])[\s:：,，\-–—…]*"
    rf"(?P<portion>{_ABOUT}(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?{_MORE}{_PAREN}{_PREP}|{_TASTE_WORDS}{_PAREN})$",
    re.I,
)
# Amount at the start: "300g 雞腿", "2 cloves garlic", "2 eggs", "兩顆蛋", "1 cup of rice"
_PORTION_START = re.compile(
    rf"^(?P<portion>{_ABOUT}(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?)\s*(?:of\s+)?(?P<name>\S.*)$",
    re.I,
)
_BULLET = re.compile(r"^\s*(?:[-–—•*·▪◦●○→>✓✔]+|\d{1,2}\s*[.)、](?!\d))\s*")
_MULTIPLIER = re.compile(r"^(\d+(?:\.\d+)?)\s*[x×]\s+", re.I)


@dataclass
class Ingredient:
    name: str
    portion: str | None = None  # as typed, shown to people: "300g", "1瓣", "少許"
    amount: float | None = None  # read from the portion, for grocery merging
    qty: str | None = None
    unit: str | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def parse_portion(portion: str | None) -> dict:
    """'300g' -> amount 300, unit g. '1/2 杯' -> 0.5 杯. '少許' -> note. Never fails."""
    text = (portion or "").strip()
    out = {"portion": text or None, "amount": None, "qty": None, "unit": None, "note": None}
    if not text:
        return out
    m = re.match(rf"^{_ABOUT}(?P<qty>{ASCII_QTY}|{ZH_QTY})\s*(?P<unit>{UNIT})?\s*(?P<rest>.*)$", text, re.I)
    if m and (m["unit"] or not m["rest"] or not re.match(r"^[A-Za-z㐀-鿿]", m["rest"])):
        out["qty"] = m["qty"].strip()
        out["amount"] = parse_qty(m["qty"])
        out["unit"] = m["unit"].strip().rstrip(".") if m["unit"] else None
        rest = m["rest"].strip()

        # "1大匙 + 1小匙" -> 4 tsp, when every part converts to the same base unit
        extra = list(re.finditer(rf"[+＋]\s*(?P<q>{ASCII_QTY}|{ZH_QTY})\s*(?P<u>{UNIT})?", rest, re.I))
        if extra:
            base, factor = base_unit(out["unit"])
            parts = [(out["amount"], factor)]
            for e in extra:
                b, f = base_unit(e["u"].strip().rstrip(".") if e["u"] else None)
                parts.append((parse_qty(e["q"]) if b == base else None, f))
            if all(a is not None for a, _ in parts):
                out["amount"] = sum(a * f for a, f in parts)
                out["qty"], out["unit"] = None, base
            rest = rest[extra[-1].end():] if extra[0].start() == 0 else rest

        out["note"] = rest.strip(" ,，()（）") or None
        return out
    out["note"] = text
    return out


def parse_line(line: str) -> Ingredient | None:
    """Split one ingredient line into name + portion. Returns None for a blank line."""
    text = _BULLET.sub("", line).strip()
    text = _MULTIPLIER.sub(r"\1 ", text)
    if not text:
        return None

    m = _PORTION_END.match(text)
    if m and not (m["qty"] and _is_zh_qty(m["qty"]) and not m["unit"]):
        return _make(m["name"], m["portion"])

    m = _PORTION_START.match(text)
    if m and m["name"].strip() and not (_is_zh_qty(m["qty"]) and not m["unit"]):
        return _make(m["name"], m["portion"])

    return Ingredient(name=text)


def _make(name: str, portion: str) -> Ingredient:
    p = parse_portion(portion)
    return Ingredient(name=name.strip(" ,，:："), **p)


def parse_lines(text: str) -> list[Ingredient]:
    """One ingredient per line. Nothing is split on commas, nothing is dropped."""
    return [ing for ln in text.replace("\r\n", "\n").split("\n") if (ing := parse_line(ln))]


def ingredient_from_fields(name: str, portion: str | None) -> Ingredient:
    """From the one-by-one editor: the name and portion are already separate."""
    return Ingredient(name=name.strip(), **parse_portion(portion))


def portion_text(qty: str | None, unit: str | None, note: str | None) -> str | None:
    """Rebuild a portion for ingredients saved before portions existed ("2 cloves", "3瓣", "少許")."""
    text = qty or ""
    if unit:
        text = f"{text}{unit}" if re.match(r"[\u3400-\u9fff]", unit) else f"{text} {unit}".strip()
    if note:
        text = f"{text}, {note}" if text else note
    return text or None


def normalize_ingredient(data: dict, has_portion: bool) -> dict:
    """What we store for one ingredient: name, portion as typed, and the parsed amount."""
    if has_portion:
        return ingredient_from_fields(data["name"], data.get("portion")).to_dict()
    out = {k: data.get(k) for k in ("name", "amount", "qty", "unit", "note")}
    out["name"] = (out["name"] or "").strip()
    out["portion"] = portion_text(out["qty"], out["unit"], out["note"])
    return out
