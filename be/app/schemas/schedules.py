from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ---------- /api/users/schedules /init ----------
# Input (Plan API 스타일로 완전 교체)
class DateIn(BaseModel):
    user_id: str
    start_date: str
    end_date: str
    arrival_time: str
    departure_time: str
    start_place: str
    end_place: str

class UserPrefIn(BaseModel):
    start_time: str
    end_time: str
    travel_style: str
    meal_time_preferences: Dict[str, List[str]]
    tags: List[str]

# PlaceNameIn을 먼저 정의 (places_by_day용)
class PlaceNameIn(BaseModel):
    name: str

class InitRequest(BaseModel):
    # Init API 기존 필드들
    date: DateIn
    user: UserPrefIn
    places_by_day: Optional[Dict[int, List[PlaceNameIn]]] = None  # 기존 init 방식 (선택적)

    # Plan API 필드들 추가
    start_transport_id: Optional[int] = None
    end_transport_id: Optional[int] = None
    total_days: Optional[int] = None  # date에서 계산 가능
    daily_locations: Optional[List[int]] = None  # 지역 코드 리스트
    hashtags: Optional[List[str]] = None  # user.tags와 동일할 수 있음
    use_mock: Optional[bool] = False

# Output (Plan API 스타일로 완전 교체)
class DaySchedule(BaseModel):
    day: int
    date: str  # "2025-09-29" 형식
    visits: List[Dict[str, Any]]  # 방문지 + 시간 정보
    path: List[List[List[float]]] = []  # 경로 정보

    # 오류 추적 정보 (선택적)
    selection_errors: Optional[List[Dict[str, Any]]] = []
    selection_summary: Optional[Dict[str, Any]] = {}
    retry_history: Optional[List[Dict[str, Any]]] = []

class InitResponse(BaseModel):
    success: bool = True
    error: Optional[str] = None
    total_days: int
    start_date: str
    end_date: str
    day_schedules: List[DaySchedule]

    class Config:
        from_attributes = True


# ---------- /api/users/schedules /schedul ----------
# Input (명세는 GET+Body 구조지만, 스키마는 그대로 둠)
class PlaceWithServiceIn(BaseModel):
    name: str
    service_time: int

class SchedulRequest(BaseModel):
    user_id: str
    places_by_day: Dict[int, List[PlaceWithServiceIn]]

# Output
class PlaceWithTimingOut(BaseModel):
    name: str
    category: str
    address: str
    arrival_str: str
    departure_str: str
    service_time: int
    x_cord: float
    y_cord: float

class SchedulResponse(BaseModel):
    places_by_day: Dict[int, List[PlaceWithTimingOut]]
    path: List[List[List[float]]]  # [[[x,y], [x,y]], ...]

    class Config:
        from_attributes = True


# ---------- /api/users/schedules /itinerary ----------
# Input
class PlaceItineraryIn(BaseModel):
    name: str
    arrival_str: str
    departure_str: str
    service_time: int

class ItineraryRequest(BaseModel):
    places_by_day: Dict[int, List[PlaceItineraryIn]]

# Output
class PlaceItineraryOut(BaseModel):
    name: str
    address: str
    category: str
    open_time: str = ""
    close_time: str = ""
    convenience: List[str]
    arrival_str: str
    departure_str: str
    service_time: int
    description: str
    image_urls: List[str]

class ItineraryResponse(BaseModel):
    places_by_day: Dict[int, List[PlaceItineraryOut]]

    class Config:
        from_attributes = True
