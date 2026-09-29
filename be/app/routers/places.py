from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from app.database import get_db

from app.models.jeju_cafe import JejuCafe
from app.models.jeju_hotel import JejuHotel
from app.models.jeju_restaurant import JejuRestaurant
from app.models.jeju_tour import JejuTour
from app.models.jeju_transport import JejuTransport

from app.schemas.places import SelectPlaceResponse, PlaceDetail, SearchOut, SearchOutItem
from ._utils import to_float, parse_image_url

router = APIRouter(prefix="/api/places", tags=["places"])

MODEL_INFO = {
    "cafe": JejuCafe,
    "hotel": JejuHotel,
    "restaurant": JejuRestaurant,
    "tour": JejuTour,
    "transport": JejuTransport,
}

def _find_any_by_name(db: Session, name: str):
    # 정확 일치 우선 → 부분 일치
    for div, Model in MODEL_INFO.items():
        r = db.query(Model).filter(func.lower(Model.name) == func.lower(name.strip())).first()
        if r:
            return div, r
    like = f"%{name.strip()}%"
    for div, Model in MODEL_INFO.items():
        r = db.query(Model).filter(func.lower(Model.name).like(func.lower(like))).first()
        if r:
            return div, r
    return None, None

@router.get("/select_place", response_model=SelectPlaceResponse)
def select_place(name: str = Query(..., description="place name"), db: Session = Depends(get_db)):
    div, row = _find_any_by_name(db, name)
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")

    imgs = parse_image_url(getattr(row, "image_url", None)) or []
    data = PlaceDetail(
        name=row.name,
        category=div,
        address=row.address or "",
        x_cord=to_float(row.x_cord) or 0.0,
        y_cord=to_float(row.y_cord) or 0.0,
        open_time=row.open_time or "",
        close_time=row.close_time or "",
        convenience=row.convenience or "",
        image_urls=imgs
    )
    return SelectPlaceResponse(places=data)

@router.get("/search", response_model=SearchOut)
def search(name: str = Query(..., description="search keyword"), db: Session = Depends(get_db)):
    like = f"%{name.strip()}%"
    names: List[str] = []

    for Model in MODEL_INFO.values():
        rows = (
            db.query(Model.name)
            .filter(or_(
                func.lower(Model.name).like(func.lower(like)),
                func.lower(Model.category).like(func.lower(like)),
                func.lower(Model.address).like(func.lower(like)),
            ))
            .limit(50)
            .all()
        )
        names.extend([r[0] for r in rows if r and r[0]])

    uniq = []
    seen = set()
    for nm in names:
        if nm not in seen:
            seen.add(nm)
            uniq.append(nm)
        if len(uniq) >= 50:
            break

    return SearchOut(search=[SearchOutItem(name=n) for n in uniq])
