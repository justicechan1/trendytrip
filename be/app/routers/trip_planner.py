from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os
import json
from datetime import datetime

# TripScheduler 모듈 임포트 - 절대 경로 사용
trip_scheduler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'TripScheduler'))
if trip_scheduler_path not in sys.path:
    sys.path.insert(0, trip_scheduler_path)

from tripscheduler.scheduler_api import schedule_trip

router = APIRouter(prefix="/api/trip-planner", tags=["trip-planner"])


class PlaceInput(BaseModel):
    id: int  # int로 변경
    name: str
    x_cord: float
    y_cord: float
    category: Optional[str] = None
    service_time: Optional[int] = 0
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    tags: Optional[List[str]] = []
    is_mandatory: Optional[bool] = False
    closed_days: Optional[List] = []
    break_time: Optional[List] = []

class UserInput(BaseModel):
    start_time: str
    end_time: str
    travel_style: Optional[str] = "normal"
    meal_time_preferences: Optional[Dict[str, List[str]]] = None

class DayInfoInput(BaseModel):
    type: Optional[str] = "normal"  
    start_location: Optional[Dict[str, Any]] = None
    end_location: Optional[Dict[str, Any]] = None
    is_first_day: Optional[bool] = False
    is_last_day: Optional[bool] = False
    date: Optional[str] = None
    weekday: Optional[str] = None

class TripScheduleRequest(BaseModel):
    places: List[PlaceInput]
    user: UserInput
    day_info: DayInfoInput
    use_mock: Optional[bool] = False

class TripScheduleResponse(BaseModel):
    visits: List[Dict[str, Any]]
    path: List[List[List[float]]]

@router.post("/schedule", response_model=TripScheduleResponse)
async def create_trip_schedule(request: TripScheduleRequest):
    """
    여행 일정을 최적화하여 생성합니다.
    """
    try:
        print(f"[DEBUG] Schedule API 호출됨")

        # Pydantic 모델을 dict로 변환
        data = {
            "places": [place.model_dump() for place in request.places],
            "user": request.user.model_dump(),
            "day_info": request.day_info.model_dump()
        }

        print(f"[DEBUG] 변환된 데이터: {data}")

        # TripScheduler 실행 시도
        try:
            print(f"[DEBUG] TripScheduler 실행 시도")

            # meal_time_preferences가 None인 경우 기본값 설정
            if data["user"]["meal_time_preferences"] is None:
                data["user"]["meal_time_preferences"] = {
                    "lunch": ["12:00", "13:30"],
                    "dinner": ["18:00", "19:30"]
                }
                print(f"[DEBUG] meal_time_preferences 기본값 설정: {data['user']['meal_time_preferences']}")

            result = schedule_trip(
                data=data,
                use_mock=request.use_mock
            )

            # 결과가 유효한지 확인
            if result and result.get("visits"):
                print(f"[DEBUG] 스케줄러 성공: visits 개수 = {len(result.get('visits', []))}")
                return TripScheduleResponse(**result)
            else:
                print(f"[DEBUG] 스케줄러 결과가 비어있음: {result}")
                print(f"[DEBUG] 기본 응답 사용")
        except Exception as scheduler_error:
            import traceback
            print(f"[DEBUG] 스케줄러 오류: {scheduler_error}")
            print(f"[DEBUG] 상세 오류: {traceback.format_exc()}")
            print(f"[DEBUG] 기본 응답으로 폴백")

        # 스케줄러 실패 시 기본 응답 생성
        print(f"[DEBUG] 기본 응답 생성")

        visits = []
        path = []

        # 사용자가 설정한 시작 시간 파싱
        try:
            start_time_parts = request.user.start_time.split(":")
            user_start_minutes = int(start_time_parts[0]) * 60 + int(start_time_parts[1])
        except:
            user_start_minutes = 8 * 60  # 기본값: 8:00

        # 장소들을 기본 순서로 배치
        for i, place in enumerate(request.places):
            # 사용자 시작 시간부터 각 장소마다 service_time + 이동시간 계산
            start_minutes = user_start_minutes + i * 60
            end_minutes = start_minutes + (place.service_time or 60)

            start_hour = start_minutes // 60
            start_min = start_minutes % 60
            end_hour = end_minutes // 60
            end_min = end_minutes % 60

            visit = {
                "order": i + 1,
                "place": place.name,
                "arrival_str": f"{start_hour:02d}:{start_min:02d}",
                "departure_str": f"{end_hour:02d}:{end_min:02d}",
                "stay_duration": f"{(place.service_time or 60) // 60:02d}:{(place.service_time or 60) % 60:02d}",
                "x_cord": place.x_cord,
                "y_cord": place.y_cord
            }
            visits.append(visit)

            # 경로 추가
            if i > 0:
                path.append([[prev_place.x_cord, prev_place.y_cord], [place.x_cord, place.y_cord]])
            prev_place = place

        fallback_result = {
            "visits": visits,
            "path": path
        }

        print(f"[DEBUG] 기본 응답 반환: {fallback_result}")
        return TripScheduleResponse(**fallback_result)

    except Exception as e:
        print(f"[DEBUG] 에러 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Trip scheduling failed: {str(e)}"
        )

@router.post("/schedule/mock", response_model=TripScheduleResponse)
async def create_trip_schedule_mock(request: TripScheduleRequest):
    """
    모의 데이터를 사용하여 여행 일정을 생성합니다.
    """

    try:
        # Pydantic 모델을 dict로 변환
        data = {
            "places": [place.model_dump() for place in request.places],
            "user": request.user.model_dump(),
            "day_info": request.day_info.model_dump()
        }

        # 모의 데이터로 TripScheduler 실행
        result = schedule_trip(
            data=data,
            use_mock=True
        )


        return TripScheduleResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mock trip scheduling failed: {str(e)}"
        )