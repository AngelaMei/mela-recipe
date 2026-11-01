"""Read a YouTube video's description (only ingredients and steps are imported)."""

from __future__ import annotations

import re
import time
from urllib.parse import parse_qs, urlparse

import httpx

from ..config import get_settings

_CACHE: dict[str, tuple[float, str]] = {}
_TTL = 15 * 60


class YouTubeUnavailable(Exception):
    pass


def video_id(url: str) -> str | None:
    if not re.match(r"^https?://", url):
        url = "https://" + url
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host.endswith("youtu.be"):
        vid = parsed.path.strip("/").split("/")[0]
        return vid or None
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        m = re.match(r"^/(?:shorts|embed|live|v)/([\w-]{6,})", parsed.path)
        if m:
            return m[1]
    return None


def fetch_description(url: str) -> str:
    vid = video_id(url)
    if not vid:
        raise YouTubeUnavailable("not a video link")
    cached = _CACHE.get(vid)
    if cached and time.monotonic() - cached[0] < _TTL:
        return cached[1]

    key = get_settings().youtube_api_key
    if not key:
        raise YouTubeUnavailable("YOUTUBE_API_KEY is not set")
    try:
        resp = httpx.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet", "id": vid, "key": key},
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items") or []
    except (httpx.HTTPError, ValueError) as exc:
        raise YouTubeUnavailable(str(exc)) from exc
    if not items:
        raise YouTubeUnavailable("video not found")
    description = items[0].get("snippet", {}).get("description", "") or ""
    _CACHE[vid] = (time.monotonic(), description)
    return description
