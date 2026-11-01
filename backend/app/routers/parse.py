from fastapi import APIRouter, Depends

from ..auth import current_member
from ..schemas import LinesIn, ParseIn
from ..services.lines import parse_lines, portion_text
from ..services import youtube
from ..services.parsing import SplitOptions, detect_source, parse_recipe

router = APIRouter(prefix="/api", tags=["parse"], dependencies=[Depends(current_member)])


@router.post("/parse")
def parse(body: ParseIn):
    """Live preview for the Add screen.

    status: ok | empty (nothing found) | link_only | needs_caption | fetch_failed
    """
    text = body.input.strip()
    source = detect_source(text)
    opts = SplitOptions(**body.split.model_dump())
    url = text if source in ("youtube", "instagram", "link") else None
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    content: str | None = None
    status = "ok"
    if source == "text":
        content = text
    elif source == "youtube":
        if body.caption and body.caption.strip():
            content = body.caption
        else:
            try:
                content = youtube.fetch_description(text)
            except youtube.YouTubeUnavailable:
                status = "fetch_failed"
    elif source == "instagram":
        content = body.caption if body.caption and body.caption.strip() else None
        if content is None:
            status = "needs_caption"
    else:
        status = "link_only"

    parsed = parse_recipe(content, opts) if content else None
    ingredients = (
        [{**i.to_dict(), "portion": portion_text(i.qty, i.unit, i.note)} for i in parsed.ingredients]
        if parsed
        else []
    )
    steps = parsed.steps if parsed else []
    if status == "ok" and not ingredients and not steps:
        status = "empty"
    return {
        "source": source,
        "url": url,
        "status": status,
        "ingredients": ingredients,
        "steps": steps,
    }


@router.post("/parse/lines")
def parse_ingredient_lines(body: LinesIn):
    """The ingredient box: one ingredient per line -> name + portion, for the live preview."""
    return {"ingredients": [i.to_dict() for i in parse_lines(body.text)]}
