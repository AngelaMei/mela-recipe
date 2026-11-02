"""Household auth: pick who you are + a shared passcode -> signed cookie."""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import Settings, get_settings

COOKIE = "mela_session"


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    if len(settings.session_secret) < 16:  # also refused at startup (main.config_problems)
        raise HTTPException(status_code=500, detail="SESSION_SECRET must be at least 16 characters")
    return URLSafeTimedSerializer(settings.session_secret, salt="mela-session")


def check_passcode(settings: Settings, passcode: str) -> bool:
    if not settings.mela_passcode:  # never allow an empty passcode
        return False
    return hmac.compare_digest(passcode.encode(), settings.mela_passcode.encode())


def set_session(response: Response, settings: Settings, member: str) -> None:
    token = _serializer(settings).dumps({"m": member})
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


def current_member(request: Request, settings: Settings = Depends(get_settings)) -> str:
    token = request.cookies.get(COOKIE)
    if token:
        try:
            data = _serializer(settings).loads(token, max_age=settings.session_days * 86400)
        except BadSignature:
            data = None
        names = {m["name"] for m in settings.members}
        if data and data.get("m") in names:
            return data["m"]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in")
