"""Import past recipes. The formats are documented in docs/import-format.md.

- Markdown / plain text (.md, .txt): "## Recipe name" headings with
  "### Ingredients" and "### Steps" sections. The recipes.md in a Mela export
  uses this layout, so it imports back as-is.
- Mela backup (.zip from Settings > Backup, or its mela-backup.json): restores
  recipes, cook logs and photos.
- JSON (.json): a list of recipes, for converting from other apps with a script.

parse_upload() only reads; apply_import() writes. The import screen shows the
parse result as a preview before anything is saved.
"""

from __future__ import annotations

import io
import json
import re
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime

from .lines import ingredient_from_fields, parse_line
from .parsing import detect_source

MAX_RECIPES = 2000

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class ImportedLog:
    cooked_on: date
    rating: int | None = None
    note: str | None = None
    tweaks: str | None = None
    created_by: str | None = None
    photo: tuple[bytes, str] | None = None  # (data, content type)
    photo_crop: dict | None = None
    created_at: datetime | None = None


@dataclass
class ImportedRecipe:
    name: str
    name_alt: str | None = None
    source: str = "manual"
    source_url: str | None = None
    note: str | None = None
    ingredients: list[dict] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    plate_id: str | None = None
    logs: list[ImportedLog] = field(default_factory=list)
    id: uuid.UUID | None = None  # from a Mela backup
    created_by: str | None = None
    created_at: datetime | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    recipes: list[ImportedRecipe] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    kind: str = "markdown"  # markdown | backup | json


class ImportError_(ValueError):
    """The file can't be read at all (wrong type, broken zip, invalid JSON)."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_URL = re.compile(r"https?://\S+")
_STEP_PREFIX = re.compile(r"^\s*(?:[-*•·]+|(?:step\s*)?\d{1,3}\s*[.)、:：](?!\d)|[①-⑳])\s*", re.I)
_BULLET = re.compile(r"^\s*[-*•·]\s+")
_PORTION_SEP = re.compile(r"\s+[—–|]\s+|\s*[｜]\s*")
_DATE = re.compile(r"(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?")
_SECTION_NAMES = {
    "ingredients": r"ingredients?|食材|材料|準備材料",
    "steps": r"steps?|method|directions|instructions|how to make|作法|做法|步驟",
    "log": r"cook\s*log|cooking\s*log|log|history|紀錄|記錄|料理紀錄|做過",
}


def _clean(value) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _parse_date(text: str) -> date | None:
    m = _DATE.search(text)
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def ingredient_from_text(line: str) -> dict | None:
    """'雞腿 — 300g' (explicit) or '雞腿 300g' / '2 cloves garlic' (split by the usual rule)."""
    text = _BULLET.sub("", line).strip()
    if not text:
        return None
    parts = _PORTION_SEP.split(text, maxsplit=1)
    if len(parts) == 2 and parts[0].strip():
        return ingredient_from_fields(parts[0], parts[1].strip() or None).to_dict()
    ing = parse_line(text)
    return ing.to_dict() if ing else None


def _section_kind(title: str) -> str | None:
    t = title.strip().strip(":：").strip()
    for kind, rx in _SECTION_NAMES.items():
        if re.fullmatch(rf"(?:{rx})(?:\s*[（(].*[)）])?", t, re.I):
            return kind
    return None


def _set_link(r: ImportedRecipe, url: str) -> None:
    url = url.rstrip(").,，。")
    r.source_url = url
    src = detect_source(url)
    r.source = src if src in ("youtube", "instagram") else "link"


# ---------------------------------------------------------------------------
# Markdown / text
# ---------------------------------------------------------------------------
def parse_markdown(text: str, filename: str = "") -> ParseResult:
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    lines = text.split("\n")
    result = ParseResult(kind="markdown")

    # Recipes are "## " headings. A file that only uses "# " headings uses those;
    # a file with no headings at all is one recipe named after the file.
    level = "## " if any(l.startswith("## ") for l in lines) else "# " if any(l.startswith("# ") for l in lines) else None
    chunks: list[tuple[str, list[str]]] = []
    if level is None:
        stem = re.sub(r"\.[^.]+$", "", filename.rsplit("/", 1)[-1]) or "Untitled recipe"
        chunks.append((stem, lines))
    else:
        current: tuple[str, list[str]] | None = None
        for line in lines:
            if line.startswith(level):
                current = (line[len(level):].strip(), [])
                chunks.append(current)
            elif current is not None:
                current[1].append(line)
            # anything before the first recipe heading (a file title, an intro) is ignored

    for title, body in chunks:
        result.recipes.append(_parse_markdown_recipe(title, body))
    return result


def _parse_markdown_recipe(title: str, body: list[str]) -> ImportedRecipe:
    r = ImportedRecipe(name=title.strip("# ").strip() or "Untitled recipe")
    section: str | None = None
    notes: list[str] = []
    unknown_sections: list[str] = []

    for raw in body:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            continue
        heading = re.match(r"^#{3,6}\s+(.*)$", stripped)
        if heading:
            kind = _section_kind(heading[1])
            if kind:
                section = kind
            elif section == "ingredients":
                pass  # a sub-heading such as "#### Sauce" inside the ingredients
            else:
                section = "other"
                unknown_sections.append(heading[1].strip())
            continue

        if section is None:  # details between the name and the first section
            m = re.match(r"^(?:link|source|url|連結|來源|網址)\s*[:：]\s*(.+)$", stripped, re.I)
            if m:
                urls = _URL.findall(m[1])
                if urls:
                    _set_link(r, urls[0])
                continue
            m = re.match(r"^(?:note|notes|備註|筆記)\s*[:：]\s*(.+)$", stripped, re.I)
            if m:
                notes.append(m[1].strip())
                continue
            m = re.match(r"^(?:name in .+|other name|alt(?:ernative)? name|英文名|中文名|別名)\s*[:：]\s*(.+)$", stripped, re.I)
            if m:
                r.name_alt = m[1].strip()
                continue
            m = re.match(r"^(?:plate|盤子)\s*[:：]\s*([\w-]+)\s*$", stripped, re.I)
            if m:
                r.plate_id = m[1].lower()
                continue
            m = re.fullmatch(r"\*([^*]+)\*|_([^_]+)_", stripped)
            if m and not r.name_alt:
                r.name_alt = (m[1] or m[2]).strip()
                continue
            if stripped.startswith(">"):
                notes.append(stripped.lstrip("> ").strip())
                continue
            urls = _URL.findall(stripped)
            if urls and not r.source_url:
                _set_link(r, urls[0])
            if re.match(r"^(made \d+×|not made yet|做過 \d+ 次|還沒做過)", stripped, re.I):
                continue  # the summary line in Mela's own export
            if not urls:
                notes.append(stripped)
            continue

        if section == "ingredients":
            ing = ingredient_from_text(stripped)
            if ing:
                r.ingredients.append(ing)
        elif section == "steps":
            if raw[:1] in (" ", "\t") and r.steps and not _STEP_PREFIX.match(raw):
                r.steps[-1] = f"{r.steps[-1]} {stripped}"  # an indented continuation line
            else:
                step = _STEP_PREFIX.sub("", stripped).strip()
                if step:
                    r.steps.append(step)
        elif section == "log":
            log = _parse_log_line(stripped)
            if log:
                r.logs.append(log)
            else:
                r.warnings.append(f"Cook log line without a date was skipped: {stripped[:60]}")

    if notes:
        r.note = "\n".join(notes)
    for name in unknown_sections:
        r.warnings.append(f"Section “{name}” isn't ingredients, steps or cook log, so it was skipped")
    if not r.ingredients and not r.steps and not r.source_url:
        r.warnings.append("No ingredients, steps or link found")
    return r


def _parse_log_line(line: str) -> ImportedLog | None:
    """'- 2026-10-24 ★★★★ (Mei): Less sugar next time. Tweaks: added vinegar'"""
    text = _BULLET.sub("", line).strip()
    when = _parse_date(text)
    if not when:
        return None
    rest = _DATE.sub("", text, count=1).strip()
    rating = None
    m = re.match(r"^([★☆]+)", rest)
    if m:
        rating = m[1].count("★") or None
        rest = rest[m.end():].strip()
    else:
        m = re.match(r"^(\d)\s*/\s*5\b|^(\d)\s*(?:stars?|星|分)", rest, re.I)
        if m:
            rating = int(m[1] or m[2])
            rest = rest[m.end():].strip()
    who = None
    m = re.match(r"^[（(]([^()（）]{1,40})[)）]", rest)
    if m:
        who = m[1].strip()
        rest = rest[m.end():].strip()
    rest = rest.lstrip(":：-–— ").strip()
    tweaks = None
    m = re.search(r"\b(?:tweaks?|調整)\s*[:：]\s*(.+)$", rest, re.I)
    if m:
        tweaks = m[1].strip()
        rest = rest[: m.start()].strip()
    if rating is not None and not 1 <= rating <= 5:
        rating = None
    return ImportedLog(cooked_on=when, rating=rating, note=rest or None, tweaks=tweaks, created_by=who)


# ---------------------------------------------------------------------------
# JSON (Mela backup or a plain list)
# ---------------------------------------------------------------------------
def parse_json(data, photos: dict[str, bytes] | None = None) -> ParseResult:
    photos = photos or {}
    if isinstance(data, dict) and data.get("format") == "mela-backup":
        kind = "backup"
        items = data.get("recipes") or []
    elif isinstance(data, dict) and isinstance(data.get("recipes"), list):
        kind, items = "json", data["recipes"]
    elif isinstance(data, list):
        kind, items = "json", data
    else:
        raise ImportError_("JSON must be a list of recipes, or an object with a \"recipes\" list")

    result = ParseResult(kind=kind)
    for n, item in enumerate(items, 1):
        if not isinstance(item, dict) or not _clean(item.get("name") or item.get("title")):
            result.warnings.append(f"Item {n} has no name, so it was skipped")
            continue
        result.recipes.append(_recipe_from_json(item, photos, kind == "backup"))
    return result


def _recipe_from_json(item: dict, photos: dict[str, bytes], backup: bool) -> ImportedRecipe:
    r = ImportedRecipe(name=_clean(item.get("name") or item.get("title")) or "Untitled recipe")
    r.name_alt = _clean(item.get("name_alt") or item.get("alt_name"))
    r.note = _clean(item.get("note") or item.get("notes"))
    url = _clean(item.get("source_url") or item.get("url") or item.get("link"))
    if url:
        _set_link(r, url)
    if backup and item.get("source") in ("youtube", "instagram", "link", "manual"):
        r.source = item["source"]
    r.plate_id = _clean(item.get("plate_id") or item.get("plate"))

    ings = item.get("ingredients") or []
    if isinstance(ings, str):
        ings = ings.split("\n")
    for ing in ings:
        if isinstance(ing, str):
            parsed = ingredient_from_text(ing)
        elif isinstance(ing, dict) and _clean(ing.get("name")):
            if "portion" in ing or not any(k in ing for k in ("qty", "unit", "amount")):
                parsed = ingredient_from_fields(ing["name"], _clean(ing.get("portion") or ing.get("amount_text"))).to_dict()
            else:  # older Mela ingredient objects
                parsed = {k: ing.get(k) for k in ("name", "amount", "qty", "unit", "note")}
                parsed["portion"] = ing.get("portion")
        else:
            parsed = None
        if parsed:
            r.ingredients.append(parsed)

    steps = item.get("steps") or item.get("instructions") or []
    if isinstance(steps, str):
        steps = steps.split("\n")
    for s in steps:
        text = s.get("text") if isinstance(s, dict) else s
        text = _STEP_PREFIX.sub("", str(text or "")).strip()
        if text:
            r.steps.append(text)

    for lg in item.get("logs") or item.get("cook_log") or []:
        if not isinstance(lg, dict):
            continue
        when = _parse_date(str(lg.get("cooked_on") or lg.get("date") or ""))
        if not when:
            r.warnings.append("A cook log entry without a date was skipped")
            continue
        rating = lg.get("rating")
        log = ImportedLog(
            cooked_on=when,
            rating=rating if isinstance(rating, int) and 1 <= rating <= 5 else None,
            note=_clean(lg.get("note")),
            tweaks=_clean(lg.get("tweaks")),
            created_by=_clean(lg.get("created_by") or lg.get("by")),
            photo_crop=lg.get("photo_crop") if isinstance(lg.get("photo_crop"), dict) else None,
            created_at=_parse_dt(lg.get("created_at")),
        )
        path = lg.get("photo")
        if isinstance(path, str) and path:
            if path in photos:
                ext = path.rsplit(".", 1)[-1].lower()
                ctype = {"png": "image/png", "webp": "image/webp", "heic": "image/heic", "heif": "image/heif"}.get(ext, "image/jpeg")
                log.photo = (photos[path], ctype)
            else:
                r.warnings.append(f"Photo {path} isn't in the file, so that cook is imported without it")
        r.logs.append(log)

    if backup:
        try:
            r.id = uuid.UUID(str(item.get("id")))
        except ValueError:
            r.id = None
        r.created_by = _clean(item.get("created_by"))
        r.created_at = _parse_dt(item.get("created_at"))
    if not r.ingredients and not r.steps and not r.source_url:
        r.warnings.append("No ingredients, steps or link found")
    return r


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _decode(data: bytes) -> str:
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):  # UTF-16 with a byte-order mark (e.g. Windows Notepad)
        return data.decode("utf-16")
    # Traditional Chinese text from older Windows tools is often Big5
    for enc in ("utf-8-sig", "big5", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ImportError_("The file isn't readable text. Save it as UTF-8.")


def parse_upload(filename: str, data: bytes) -> ParseResult:
    name = (filename or "").lower()
    if name.endswith(".zip") or data[:4] == b"PK\x03\x04":
        return _parse_zip(data)
    if name.endswith(".json"):
        try:
            return parse_json(json.loads(_decode(data)))
        except json.JSONDecodeError as exc:
            raise ImportError_(f"The JSON isn't valid (line {exc.lineno}): {exc.msg}") from exc
    if name.endswith((".md", ".markdown", ".txt")) or not name:
        return parse_markdown(_decode(data), filename)
    raise ImportError_("Use a .md, .txt, .json or .zip file")


def _parse_zip(data: bytes) -> ParseResult:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ImportError_("The .zip file is damaged") from exc
    names = [n for n in zf.namelist() if not n.endswith("/") and "__MACOSX" not in n]

    backup = next((n for n in names if n.rsplit("/", 1)[-1] == "mela-backup.json"), None)
    if backup:
        prefix = backup[: -len("mela-backup.json")]
        photos = {n[len(prefix):]: zf.read(n) for n in names if n.startswith(prefix + "photos/")}
        try:
            return parse_json(json.loads(zf.read(backup).decode("utf-8")), photos)
        except json.JSONDecodeError as exc:
            raise ImportError_("mela-backup.json in the .zip isn't valid JSON") from exc

    # Any other zip: every .md / .txt / .json inside
    result = ParseResult(kind="markdown")
    for n in sorted(names):
        if n.lower().endswith((".md", ".markdown", ".txt", ".json")):
            try:
                part = parse_upload(n, zf.read(n))
            except ImportError_ as exc:
                result.warnings.append(f"{n}: {exc}")
                continue
            result.recipes += part.recipes
            result.warnings += [f"{n}: {w}" for w in part.warnings]
    if not result.recipes and not result.warnings:
        raise ImportError_("The .zip has no mela-backup.json and no .md, .txt or .json files")
    return result
