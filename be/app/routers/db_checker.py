# routers/db_checker.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db

from app.models.jeju_cafe import JejuCafe
from app.models.jeju_restaurant import JejuRestaurant
from app.models.jeju_tour import JejuTour      
from app.models.jeju_hotel import JejuHotel

router = APIRouter(prefix="/api/db", tags=["DB Checker"])

PLACE_MODELS = {
    "cafe": JejuCafe,
    "restaurant": JejuRestaurant,
    "tour": JejuTour,
    "hotel": JejuHotel,
}

@router.get("/check_place")
def check_place(
    name: str = Query(..., min_length=1, description="정확/부분 일치 모두 허용"),
    db: Session = Depends(get_db),
):

    like = f"%{name.strip()}%"

    for category, Model in PLACE_MODELS.items():

        exact = (
            db.query(Model)
            .filter(func.lower(func.trim(Model.name)) == func.lower(func.trim(func.cast(name, Model.name.type)))))
        exact_row = exact.first()
        if exact_row:
            return {
                "status": "exists",
                "category": category,
                "id": getattr(exact_row, f"{category}_id", None),
                "match": "exact",
            }

        partial = (
            db.query(Model)
            .filter(func.lower(Model.name).like(func.lower(like)))
            .limit(1)
        )
        row = partial.first()
        if row:
            return {
                "status": "exists",
                "category": category,
                "id": getattr(row, f"{category}_id", None),
                "match": "partial",
            }

    return {"status": "not_found"}
