from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Dict, List
from app.database import get_db

# models
from app.models.jeju_cafe import JejuCafe
from app.models.jeju_hotel import JejuHotel
from app.models.jeju_restaurant import JejuRestaurant
from app.models.jeju_tour import JejuTour
from app.models.jeju_transport import JejuTransport

# schemas
from app.schemas.schedules import (
    InitRequest, InitResponse, DaySchedule,
    SchedulRequest, SchedulResponse, PlaceWithTimingOut,
    ItineraryRequest, ItineraryResponse, PlaceItineraryOut
)

from ._utils import to_float, parse_image_url, parse_convenience

router = APIRouter(prefix="/api/users/schedules", tags=["schedules"])

# division → (Model, id_field)
MODEL_INFO = {
    "cafe":       (JejuCafe, "cafe_id"),
    "hotel":      (JejuHotel, "hotel_id"),
    "restaurant": (JejuRestaurant, "restaurant_id"),
    "tour":       (JejuTour, "tour_id"),
    "transport":  (JejuTransport, "transport_id"),
}

# 이름으로 장소 찾기(여러 테이블 통합)
def _find_place_by_name(db: Session, name: str):
    for div, (Model, _) in MODEL_INFO.items():
        row = db.query(Model).filter(func.lower(Model.name) == func.lower(name.strip())).first()
        if row:
            return div, row
    like = f"%{name.strip()}%"
    for div, (Model, _) in MODEL_INFO.items():
        row = db.query(Model).filter(func.lower(Model.name).like(func.lower(like))).first()
        if row:
            return div, row
    return None, None


@router.post("/init", response_model=InitResponse)
async def init(req: InitRequest, db: Session = Depends(get_db)):
    """
    완전한 여행 계획을 생성합니다 (Plan API 기능 통합)
    1. 지역 코드와 태그 기반으로 적절한 장소들을 자동 선택
    2. TripScheduler로 일정을 최적화하여 완전한 스케줄 반환
    """
    try:
        # 날짜 계산
        from datetime import datetime, timedelta
        start_date = datetime.strptime(req.date.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(req.date.end_date, "%Y-%m-%d")
        total_days = (end_date - start_date).days + 1

        print(f"[DEBUG] Processing combined init request for {total_days} days")

        # 입력 데이터 결합 처리
        if req.daily_locations:
            # Plan API 방식: 지역 코드 기반 자동 선택 + TripPlanner 호출
            print("[DEBUG] Using Plan API mode (daily_locations)")
            result = _call_plan_trip(req, total_days, start_date)
        elif req.places_by_day:
            # Init API 방식: 직접 장소 지정
            print("[DEBUG] Using Init API mode (places_by_day)")
            result = _create_fallback_schedule_from_places(req, total_days, start_date)
        else:
            # 기본값 사용
            print("[DEBUG] Using default fallback")
            result = _create_fallback_schedule(req, total_days, start_date)

        if result.get('success', False):
            day_schedules = []
            for day_result in result.get('day_results', []):
                day_num = day_result.get('day_number', 0)

                # plan_trip의 day_number는 이미 1-base (1, 2, 3)
                # date 계산은 0-base로 (day 1 = +0일, day 2 = +1일)
                current_date = start_date + timedelta(days=day_num - 1)
                date_str = current_date.strftime("%Y-%m-%d")

                day_schedules.append(DaySchedule(
                    day=day_num,  # plan_trip은 이미 1-base로 반환
                    date=date_str,
                    visits=day_result.get('visits', []),
                    path=day_result.get('path', []),
                    # 오류 추적 정보 추가
                    selection_errors=day_result.get('selection_errors', []),
                    selection_summary=day_result.get('selection_summary', {}),
                    retry_history=day_result.get('retry_history', [])
                ))

            return InitResponse(
                success=True,
                total_days=total_days,
                start_date=req.date.start_date,
                end_date=req.date.end_date,
                day_schedules=day_schedules
            )
        else:
            return InitResponse(
                success=False,
                error=result.get('error', 'Trip planning failed'),
                total_days=total_days,
                start_date=req.date.start_date,
                end_date=req.date.end_date,
                day_schedules=[]
            )

    except Exception as e:
        import traceback
        print(f"[ERROR] Init endpoint failed: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")

        return InitResponse(
            success=False,
            error=f"Internal error: {str(e)}",
            total_days=1,
            start_date=req.date.start_date,
            end_date=req.date.end_date,
            day_schedules=[]
        )

# Transport ID 매핑 헬퍼 함수
def _get_transport_id(place_name: str) -> int:
    """출발지/도착지 이름을 transport_id로 변환"""
    transport_mapping = {
        "제주국제공항": 1,  # DB의 실제 ID는 1부터 시작
        "제주국제여객터미널": 2,
    }
    return transport_mapping.get(place_name, 1)

def _call_plan_trip(req: InitRequest, total_days: int, start_date):
    """plan_trip 함수를 호출하여 실제 여행 계획 생성"""
    import sys
    import os

    # TripScheduler 및 TripRecommendationSystem 경로 추가
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    trip_scheduler_path = os.path.join(base_path, 'TripScheduler')
    trip_rec_path = os.path.join(base_path, 'TripScheduler', 'TripRecommendationSystem')

    for path in [trip_scheduler_path, trip_rec_path]:
        if path not in sys.path:
            sys.path.insert(0, path)

    try:
        from TripRecommendationSystem.trip_planner_api import plan_trip

        # plan_trip 입력 데이터 구성
        input_data = {
            "total_days": total_days,
            "start_time": req.user.start_time,
            "end_time": req.user.end_time,
            "hashtags": req.user.tags if req.user.tags else [],
            "daily_locations": req.daily_locations,
            "start_date": req.date.start_date,
            "start_transport_id": _get_transport_id(req.date.start_place),
            "end_transport_id": _get_transport_id(req.date.end_place),
        }

        # use_mock 값을 request에서 가져옴 (기본값 False)
        use_mock = req.use_mock if hasattr(req, 'use_mock') and req.use_mock is not None else False

        print(f"[DEBUG] Calling plan_trip with input: {input_data}, use_mock={use_mock}")

        # plan_trip 호출
        result = plan_trip(input_data, use_mock=use_mock)

        print(f"[DEBUG] plan_trip result success: {result.get('success')}")

        return result

    except Exception as e:
        import traceback
        print(f"[ERROR] plan_trip failed: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")

        # 실패 시 fallback
        return {
            "success": False,
            "error": f"plan_trip failed: {str(e)}",
            "day_results": []
        }

def _create_fallback_schedule_from_locations(req: InitRequest, total_days: int, start_date):
    """지역 코드 기반 fallback 스케줄 생성 (Plan API 방식)"""
    from datetime import timedelta

    # 지역 코드별 장소들 (basic_3day_jeju.json 스타일)
    location_places = {
        10: [
            {"name": "제주국제공항", "category": "transport", "x_cord": 126.4959513, "y_cord": 33.5059365},
            {"name": "용두암", "category": "tour", "x_cord": 126.5158, "y_cord": 33.5156},
            {"name": "제주맛집", "category": "restaurant", "x_cord": 126.5200, "y_cord": 33.5100},
        ],
        101: [
            {"name": "성산일출봉", "category": "tour", "x_cord": 126.9424894, "y_cord": 33.4583785},
            {"name": "우도", "category": "tour", "x_cord": 126.9500, "y_cord": 33.5000},
            {"name": "해변카페", "category": "cafe", "x_cord": 126.9300, "y_cord": 33.4500},
        ],
        204: [
            {"name": "한라산", "category": "tour", "x_cord": 126.5333333, "y_cord": 33.3500000},
            {"name": "중문관광단지", "category": "tour", "x_cord": 126.4100, "y_cord": 33.2400},
            {"name": "테디베어뮤지엄", "category": "tour", "x_cord": 126.4150, "y_cord": 33.2500},
        ]
    }

    day_results = []
    for day_idx in range(total_days):
        location_code = req.daily_locations[day_idx] if day_idx < len(req.daily_locations) else 10
        places = location_places.get(location_code, location_places[10])

        visits = []
        for idx, place in enumerate(places[:3]):  # 최대 3개 장소
            arrival_hour = 9 + idx * 2
            departure_hour = arrival_hour + 1

            visits.append({
                "order": idx + 1,
                "place": place["name"],
                "arrival_str": f"{arrival_hour:02d}:00",
                "departure_str": f"{departure_hour:02d}:00",
                "x_cord": place["x_cord"],
                "y_cord": place["y_cord"],
                "category": place["category"]
            })

        day_results.append({
            "day_number": day_idx,
            "visits": visits,
            "path": []
        })

    return {
        "success": True,
        "day_results": day_results
    }

def _create_fallback_schedule_from_places(req: InitRequest, total_days: int, start_date):
    """직접 지정된 장소 기반 fallback 스케줄 생성 (Init API 방식)"""
    from datetime import timedelta

    day_results = []
    for day_idx in range(total_days):
        # 1-base로 요청이 오므로, day_idx + 1로 조회
        places_for_day = req.places_by_day.get(day_idx + 1, [])

        visits = []
        for idx, place_input in enumerate(places_for_day[:5]):  # 최대 5개 장소
            arrival_hour = 9 + idx * 2
            departure_hour = arrival_hour + 1

            # 기본 좌표 (실제로는 DB에서 조회해야 함)
            default_coord = {"x_cord": 126.5000, "y_cord": 33.5000}

            visits.append({
                "order": idx + 1,
                "place": place_input.name,
                "arrival_str": f"{arrival_hour:02d}:00",
                "departure_str": f"{departure_hour:02d}:00",
                "x_cord": default_coord["x_cord"],
                "y_cord": default_coord["y_cord"],
                "category": "unknown"
            })

        day_results.append({
            "day_number": day_idx,
            "visits": visits,
            "path": []
        })

    return {
        "success": True,
        "day_results": day_results
    }

def _create_fallback_schedule(req: InitRequest, total_days: int, start_date):
    """기본 fallback 스케줄 생성"""
    # locations가 있으면 location 방식, 없으면 기본값
    if hasattr(req, 'daily_locations') and req.daily_locations:
        return _create_fallback_schedule_from_locations(req, total_days, start_date)
    else:
        return _create_fallback_schedule_from_locations(req, total_days, start_date)  # 기본값


@router.get("/schedule", response_model=SchedulResponse)
def schedule(req: SchedulRequest = Body(...), db: Session = Depends(get_db)):
    result_places: Dict[int, List[PlaceWithTimingOut]] = {}
    path: List[List[List[float]]] = []

    for day, items in req.places_by_day.items():
        day_list: List[PlaceWithTimingOut] = []
        for it in items:
            div, row = _find_place_by_name(db, it.name)
            if not row:
                continue
            x = to_float(row.x_cord); y = to_float(row.y_cord)
            if x is None or y is None:
                continue

            day_list.append(PlaceWithTimingOut(
                name=row.name,
                category=div,
                address=row.address or "",
                arrival_str="",
                departure_str="",
                service_time=int(it.service_time),
                x_cord=x,
                y_cord=y
            ))
        result_places[int(day)] = day_list

    return SchedulResponse(places_by_day=result_places, path=path)


@router.post("/itinerary", response_model=ItineraryResponse)
def itinerary(req: ItineraryRequest, db: Session = Depends(get_db)):
    out: Dict[int, List[PlaceItineraryOut]] = {}
    for day, items in req.places_by_day.items():
        day_list: List[PlaceItineraryOut] = []
        for it in items:
            div, row = _find_place_by_name(db, it.name)
            if not row:
                continue
            x = to_float(row.x_cord); y = to_float(row.y_cord)
            imgs = parse_image_url(getattr(row, "image_url", None)) or []

            # description 없는 테이블은 None → 빈 문자열 처리
            desc = getattr(row, "description", None) or ""

            open_t = getattr(row, "open_time", None) or ""
            close_t = getattr(row, "close_time", None) or ""
            conv_list = parse_convenience(getattr(row, "convenience", None))

            day_list.append(PlaceItineraryOut(
                name=row.name,
                address=row.address or "",
                category=div,
                arrival_str=it.arrival_str,
                departure_str=it.departure_str,
                service_time=it.service_time,
                description=desc,
                image_urls=imgs,
                open_time=open_t,
                close_time=close_t,
                convenience=conv_list
            ))
        out[int(day)] = day_list
    return ItineraryResponse(places_by_day=out)
