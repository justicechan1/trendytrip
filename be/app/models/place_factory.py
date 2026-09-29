# app/models/place_factory.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from decimal import Decimal

from .jeju_restaurant import JejuRestaurant
from .jeju_cafe import JejuCafe
from .jeju_hotel import JejuHotel
from .jeju_tour import JejuTour
from .jeju_transport import JejuTransport
from .hashtag import Hashtag
from .hashtag_mapping import (
    RestaurantHashtagMap, CafeHashtagMap,
    HotelHashtagMap, TourHashtagMap
)

@dataclass
class PlaceData:
    """통일된 장소 데이터 형식"""
    id: int
    name: Optional[str] = None
    category: Optional[str] = None
    page_url: Optional[str] = None
    score: Optional[float] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    convenience: Optional[str] = None
    website: Optional[str] = None
    y_cord: Optional[float] = None  # latitude
    x_cord: Optional[float] = None  # longitude
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    break_time: Optional[str] = None
    service_time: Optional[str] = None
    closed_days: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[int] = None
    location_code: Optional[int] = None
    description: Optional[str] = None  # tour만
    hashtags: List[str] = None
    place_type: str = ""

    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []

    def get_id(self) -> int:
        """ID 반환 (PlaceScorer와의 호환성)"""
        return self.id

    def get_place_type(self) -> str:
        """장소 타입 반환 (PlaceScorer와의 호환성)"""
        return self.place_type

    @property
    def coordinates(self) -> Optional[tuple]:
        """좌표 튜플 반환 (lat, lng)"""
        if self.y_cord is not None and self.x_cord is not None:
            return (float(self.y_cord), float(self.x_cord))
        return None

    def to_tripscheduler_format(self) -> Dict[str, Any]:
        """TripScheduler 라이브러리에서 사용하는 포맷으로 변환"""
        coords = self.coordinates
        if not coords:
            raise ValueError(f"Place {self.name} has no coordinates")

        return {
            "id": str(self.id),
            "name": self.name or f"{self.place_type}_{self.id}",
            "y_cord": coords[0],  # latitude
            "x_cord": coords[1],  # longitude
            "category": "accommodation" if self.place_type == "hotel" else (self.category or self.place_type),
            "open_time": self.open_time or "09:00",
            "close_time": self.close_time or "18:00",
            "break_time": self.break_time,
            "service_time": int(self.service_time) if self.service_time and self.service_time.isdigit() else 60,
            "closed_days": self.closed_days,
            "score": self.score or 0.0,
            "address": self.address,
            "hashtags": self.hashtags
        }

class UnifiedPlaceFactory:
    """통합된 장소 팩토리 - SQLAlchemy 모델 사용"""

    PLACE_MODELS = {
        'restaurant': JejuRestaurant,
        'cafe': JejuCafe,
        'hotel': JejuHotel,
        'tour': JejuTour,
        'transport': JejuTransport
    }

    HASHTAG_MODELS = {
        'restaurant': RestaurantHashtagMap,
        'cafe': CafeHashtagMap,
        'hotel': HotelHashtagMap,
        'tour': TourHashtagMap,
        'transport': None  # transport는 해시태그 없음
    }

    ID_FIELDS = {
        'restaurant': 'restaurant_id',
        'cafe': 'cafe_id',
        'hotel': 'hotel_id',
        'tour': 'tour_id',
        'transport': 'transport_id'
    }

    @classmethod
    def get_places_by_location_with_hashtags(
        cls,
        db: Session,
        location_code: int,
        place_types: Optional[List[str]] = None,
        limit_per_type: int = 100
    ) -> Dict[str, List[PlaceData]]:
        """지역 코드로 장소들을 조회 (해시태그 포함)"""
        if place_types is None:
            place_types = [t for t in cls.PLACE_MODELS.keys() if t != 'transport']

        results = {}

        for place_type in place_types:
            try:
                places = cls._get_single_type_places_with_hashtags(
                    db, place_type, location_code, limit_per_type
                )
                results[place_type] = places
                if not places:
                    print(f"[PLACE_FACTORY WARNING] 지역 코드 {location_code}에서 {place_type} 타입 장소가 없습니다 (DB 쿼리 결과 0건)")
            except Exception as e:
                print(f"[PLACE_FACTORY ERROR] {place_type} 타입 쿼리 실패 (지역: {location_code}): {e}")
                import traceback
                print(f"[PLACE_FACTORY ERROR] Traceback: {traceback.format_exc()}")
                results[place_type] = []

        return results

    @classmethod
    def _get_single_type_places_with_hashtags(
        cls,
        db: Session,
        place_type: str,
        location_code: int,
        limit: int
    ) -> List[PlaceData]:
        """단일 장소 타입에 대해 지역별 장소 + 해시태그 조회"""
        model = cls.PLACE_MODELS[place_type]
        hashtag_model = cls.HASHTAG_MODELS[place_type]
        id_field = cls.ID_FIELDS[place_type]

        # 기본 쿼리
        query = db.query(model).filter(
            getattr(model, 'location_code') == location_code,
            model.y_cord.isnot(None),
            model.x_cord.isnot(None)
        ).order_by(model.score.desc()).limit(limit)

        places_data = []

        for place in query.all():
            # 해시태그 조회
            hashtags = []
            if hashtag_model:
                hashtag_query = db.query(Hashtag.hashtag).join(
                    hashtag_model,
                    Hashtag.hashtag_id == hashtag_model.hashtag_id
                ).filter(
                    getattr(hashtag_model, id_field) == getattr(place, id_field)
                )
                hashtags = [h.hashtag for h in hashtag_query.all()]

            # PlaceData 객체 생성
            place_data = cls._convert_to_place_data(place, place_type, hashtags)
            places_data.append(place_data)

        return places_data

    @classmethod
    def _convert_to_place_data(cls, model_instance, place_type: str, hashtags: List[str]) -> PlaceData:
        """SQLAlchemy 모델 인스턴스를 PlaceData로 변환"""
        id_field = cls.ID_FIELDS[place_type]
        place_id = getattr(model_instance, id_field)

        return PlaceData(
            id=place_id,
            name=model_instance.name,
            category=model_instance.category,
            page_url=model_instance.page_url,
            score=model_instance.score,
            address=model_instance.address,
            phone=model_instance.phone,
            convenience=model_instance.convenience,
            website=model_instance.website,
            y_cord=float(model_instance.y_cord) if model_instance.y_cord else None,
            x_cord=float(model_instance.x_cord) if model_instance.x_cord else None,
            open_time=model_instance.open_time,
            close_time=model_instance.close_time,
            break_time=model_instance.break_time,
            service_time=model_instance.service_time,
            closed_days=model_instance.closed_days,
            image_url=model_instance.image_url,
            price=getattr(model_instance, 'price', None),
            location_code=getattr(model_instance, 'location_code', None),
            description=getattr(model_instance, 'description', None),
            hashtags=hashtags,
            place_type=place_type
        )

    @classmethod
    def get_all_transports(cls, db: Session) -> List[PlaceData]:
        """모든 교통 장소 조회"""
        transports = db.query(JejuTransport).filter(
            JejuTransport.name.isnot(None),
            JejuTransport.x_cord.isnot(None),
            JejuTransport.y_cord.isnot(None)
        ).all()

        transport_data = []
        for transport in transports:
            place_data = cls._convert_to_place_data(transport, 'transport', ["교통", "공항", "터미널"])
            transport_data.append(place_data)

        return transport_data

    @classmethod
    def get_place_by_id(cls, db: Session, place_type: str, place_id: int) -> Optional[PlaceData]:
        """ID로 특정 장소 조회"""
        model = cls.PLACE_MODELS[place_type]
        id_field = cls.ID_FIELDS[place_type]

        place = db.query(model).filter(getattr(model, id_field) == place_id).first()
        if not place:
            return None

        # 해시태그 조회
        hashtags = []
        hashtag_model = cls.HASHTAG_MODELS[place_type]
        if hashtag_model:
            hashtag_query = db.query(Hashtag.hashtag).join(
                hashtag_model,
                Hashtag.hashtag_id == hashtag_model.hashtag_id
            ).filter(
                getattr(hashtag_model, id_field) == place_id
            )
            hashtags = [h.hashtag for h in hashtag_query.all()]

        return cls._convert_to_place_data(place, place_type, hashtags)