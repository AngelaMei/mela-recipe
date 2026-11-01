from fastapi import APIRouter, Depends, HTTPException, Response

from ..auth import check_passcode, clear_session, current_member, set_session
from ..config import Settings, get_settings
from ..schemas import LoginIn

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _household(settings: Settings) -> dict:
    return {
        "name": settings.mela_household,
        "name_zh": settings.mela_household_zh,
        "members": settings.members,
    }


@router.get("/household")
def household(settings: Settings = Depends(get_settings)):
    return _household(settings)


@router.post("/login")
def login(body: LoginIn, response: Response, settings: Settings = Depends(get_settings)):
    names = {m["name"] for m in settings.members}
    if body.member not in names or not check_passcode(settings, body.passcode):
        raise HTTPException(status_code=401, detail="Wrong passcode")
    set_session(response, settings, body.member)
    return {"member": body.member, "household": _household(settings)}


@router.post("/logout")
def logout(response: Response):
    clear_session(response)
    return {"ok": True}


@router.get("/me")
def me(member: str = Depends(current_member), settings: Settings = Depends(get_settings)):
    return {"member": member, "household": _household(settings)}
