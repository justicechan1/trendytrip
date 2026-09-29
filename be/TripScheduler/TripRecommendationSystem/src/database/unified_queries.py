"""
통합된 데이터베이스 쿼리 모듈 - app/models 사용
TripRecommendationSystem이 app/models의 SQLAlchemy 모델을 사용하도록 함
"""

import sys
import os
from typing import List, Dict, Any, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))  # ...\TripScheduler\TripRecommendationSystem\src\database
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))  # 최상위 루트(".")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import get_db
from app.models import UnifiedPlaceFactory, PlaceData


class UnifiedPlaceSearchService:
    """통합된 장소 검색 서비스 - SQLAlchemy 사용"""

    def __init__(self):
        pass

    def get_places_by_location_with_hashtags(
        self,
        location_code: int,
        place_types: Optional[List[str]] = None,
        limit_per_type: int = 100
    ) -> Dict[str, List[PlaceData]]:
        """
        지역 코드로 장소들을 조회 (해시태그 포함)

        Args:
            location_code: 지역 코드
            place_types: 조회할 장소 타입들 (None이면 전체)
            limit_per_type: 각 타입별 최대 조회 개수

        Returns:
            Dict[str, List[PlaceData]]: 장소 타입별로 분류된 장소 리스트
        """
        db_gen = get_db()
        db = next(db_gen)

        try:
            return UnifiedPlaceFactory.get_places_by_location_with_hashtags(
                db, location_code, place_types, limit_per_type
            )
        finally:
            db.close()

    def get_all_transports(self) -> List[PlaceData]:
        """모든 교통 장소 조회"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            return UnifiedPlaceFactory.get_all_transports(db)
        finally:
            db.close()

    def get_place_by_id(self, place_type: str, place_id: int) -> Optional[PlaceData]:
        """ID로 특정 장소 조회"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            return UnifiedPlaceFactory.get_place_by_id(db, place_type, place_id)
        finally:
            db.close()

    def get_location_summary(self, location_code: int) -> Dict[str, Any]:
        """
        특정 지역의 장소 통계 정보 조회

        Args:
            location_code: 지역 코드

        Returns:
            Dict: 지역별 장소 통계
        """
        db_gen = get_db()
        db = next(db_gen)

        try:
            summary = {
                'location_code': location_code,
                'total_places': 0,
                'by_type': {}
            }

            place_types = ['restaurant', 'cafe', 'hotel', 'tour']

            for place_type in place_types:
                places = UnifiedPlaceFactory.get_places_by_location_with_hashtags(
                    db, location_code, [place_type], 1000
                )
                count = len(places.get(place_type, []))
                summary['by_type'][place_type] = count
                summary['total_places'] += count

            return summary

        finally:
            db.close()

# 편의를 위한 전역 서비스 인스턴스
unified_place_search_service = UnifiedPlaceSearchService()

def get_places_by_location(
    location_code: int,
    place_types: Optional[List[str]] = None,
    limit_per_type: int = 100
) -> Dict[str, List[PlaceData]]:
    """
    지역별 장소 검색 (해시태그 포함) - 편의 함수

    Args:
        location_code: 지역 코드
        place_types: 조회할 장소 타입들
        limit_per_type: 각 타입별 최대 조회 개수

    Returns:
        Dict[str, List[PlaceData]]: 장소 타입별 장소 리스트
    """
    return unified_place_search_service.get_places_by_location_with_hashtags(
        location_code, place_types, limit_per_type
    )

def get_transport_by_id(transport_id: int) -> Optional[PlaceData]:
    """ID로 교통 장소 조회"""
    return unified_place_search_service.get_place_by_id('transport', transport_id)

def get_all_transports() -> List[PlaceData]:
    """모든 교통 장소 조회"""
    return unified_place_search_service.get_all_transports()

def find_airport() -> Optional[PlaceData]:
    """공항 찾기"""
    transports = get_all_transports()
    for transport in transports:
        if transport.name and "공항" in transport.name:
            return transport
    return None

def find_port() -> Optional[PlaceData]:
    """항구/터미널 찾기"""
    transports = get_all_transports()
    for transport in transports:
        if transport.name and ("터미널" in transport.name or "항구" in transport.name):
            return transport
    return None