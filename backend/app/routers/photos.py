import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from ..auth import current_member
from ..config import Settings, get_settings
from ..db import get_db
from ..models import Photo

router = APIRouter(prefix="/api/photos", tags=["photos"])

ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


@router.post("", status_code=201)
async def upload(
    file: UploadFile,
    db: Session = Depends(get_db),
    member: str = Depends(current_member),
    settings: Settings = Depends(get_settings),
):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Unsupported image type")
    data = await file.read(settings.max_photo_bytes + 1)
    if len(data) > settings.max_photo_bytes:
        raise HTTPException(413, "Photo is too large")
    photo = Photo(content_type=file.content_type, data=data, created_by=member)
    db.add(photo)
    db.commit()
    return {"id": str(photo.id), "url": f"/api/photos/{photo.id}"}


@router.get("/{photo_id}")
def get_photo(photo_id: str, db: Session = Depends(get_db), member: str = Depends(current_member)):
    try:
        photo = db.get(Photo, uuid.UUID(photo_id))
    except ValueError:
        photo = None
    if not photo:
        raise HTTPException(404, "Photo not found")
    return Response(
        content=photo.data,
        media_type=photo.content_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
