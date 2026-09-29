from typing import List
from pydantic import BaseModel


# ---------- /api/places /select_place ----------
# Input은 쿼리스트링 name 이므로 별도 요청 모델 불필요
# Output
class PlaceDetail(BaseModel):
    name: str
    category: str
    address: str
    x_cord: float
    y_cord: float
    open_time: str
    close_time: str
    convenience: str
    image_urls: List[str]

class SelectPlaceResponse(BaseModel):
    places: PlaceDetail


# ---------- /api/places /search ----------
# Input은 쿼리스트링 name
# Output
class SearchOutItem(BaseModel):
    name: str

class SearchOut(BaseModel):
    search: List[SearchOutItem]
