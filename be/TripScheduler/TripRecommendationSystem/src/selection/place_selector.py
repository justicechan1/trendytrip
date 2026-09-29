"""
상위 점수 기반 장소 선택 시스템
지역별 장소 조회 -> 점수 계산 -> 상위 점수 장소 선택
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# 상대 import
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.unified_queries import get_places_by_location
from scoring.place_scorer import PlaceScorer, ScoringConfig

@dataclass
class SelectionConfig:
    """장소 선택 설정"""
    # 기본 장소 선택 개수
    restaurant_count: int = 2
    tour_count: int = 1
    cafe_count: int = 0
    hotel_count: int = 0

    # 각 타입별 최대 후보 조회 개수
    max_candidates_per_type: int = 50

    # 점수 계산 설정
    scoring_config: Optional[ScoringConfig] = None

    # 참조 해시태그 (사용자 선호도)
    reference_hashtags: List[str] = field(default_factory=list)

    # 해시태그 유사도 계산 방법
    similarity_method: str = 'embedding'

    # 참조 좌표 (시작 지점 등) - 근접성 계산용
    reference_coords: Optional[Tuple[float, float]] = None  # (y_cord, x_cord) = (lat, lon)
    
    def __post_init__(self):
        if self.scoring_config is None:
            self.scoring_config = ScoringConfig()
    
    def get_selection_counts(self) -> Dict[str, int]:
        """타입별 선택 개수 반환"""
        return {
            'restaurant': self.restaurant_count,
            'tour': self.tour_count,
            'cafe': self.cafe_count,
            'hotel': self.hotel_count
        }
    
    def get_required_types(self) -> List[str]:
        """선택이 필요한 장소 타입들 반환"""
        counts = self.get_selection_counts()
        return [place_type for place_type, count in counts.items() if count > 0]

class PlaceSelector:
    """지역별 상위 점수 장소 선택기"""
    
    def __init__(self, config: Optional[SelectionConfig] = None):
        self.config = config or SelectionConfig()
        self.scorer = PlaceScorer(self.config.scoring_config)
    
    def select_places_by_location(
        self,
        location_code: int,
        custom_config: Optional[SelectionConfig] = None
    ) -> Dict[str, Any]:
        """
        지역 코드로 상위 점수 장소들 선택

        Args:
            location_code: 지역 코드
            custom_config: 커스텀 선택 설정 (선택사항)

        Returns:
            Dict: 선택된 장소들과 상세 정보
        """
        config = custom_config or self.config

        # 1. 해당 지역의 필요한 타입별 장소들 조회
        required_types = config.get_required_types()

        # 지역별 장소 조회

        places_by_type = get_places_by_location(
            location_code=location_code,
            place_types=required_types,
            limit_per_type=config.max_candidates_per_type
        )

        # 2. 각 타입별로 점수 계산 및 상위 장소 선택
        selected_places = {}
        selection_details = {}
        errors = []  # 오류 추적

        selection_counts = config.get_selection_counts()

        for place_type in required_types:
            places = places_by_type.get(place_type, [])
            required_count = selection_counts[place_type]

            if not places:
                # 장소를 찾을 수 없음
                error_msg = f"지역 코드 {location_code}에서 {place_type} 타입의 장소를 찾을 수 없습니다 (요청: {required_count}개)"
                errors.append({
                    'type': 'EMPTY_DB_RESULT',
                    'place_type': place_type,
                    'location_code': location_code,
                    'requested_count': required_count,
                    'message': error_msg
                })
                print(f"[PLACE_SELECTOR ERROR] {error_msg}")

                selected_places[place_type] = []
                selection_details[place_type] = {
                    'candidates_found': 0,
                    'requested_count': required_count,
                    'selected_count': 0,
                    'top_scores': [],
                    'error': error_msg
                }
                continue
            
            # 점수 계산
            scored_places = self.scorer.score_places_batch(
                places=places,
                reference_hashtags=config.reference_hashtags,
                similarity_method=config.similarity_method,
                reference_coords=config.reference_coords
            )
            
            # 상위 N개 선택
            top_places = scored_places[:required_count]
            selected_places[place_type] = [result['place'] for result in top_places]
            
            # 선택 상세 정보
            selection_details[place_type] = {
                'candidates_found': len(places),
                'requested_count': required_count,
                'selected_count': len(top_places),
                'top_scores': [result['score_info']['total_score'] for result in top_places],
                'score_range': {
                    'min': min(result['score_info']['total_score'] for result in scored_places),
                    'max': max(result['score_info']['total_score'] for result in scored_places),
                    'avg': sum(result['score_info']['total_score'] for result in scored_places) / len(scored_places)
                }
            }
            
            # 선택 완료
        
        # 3. 전체 결과 구성
        total_selected = sum(len(places) for places in selected_places.values())
        total_requested = sum(selection_counts.values())

        result = {
            'location_code': location_code,
            'config': config,
            'selected_places': selected_places,
            'selection_details': selection_details,
            'summary': {
                'total_selected': total_selected,
                'total_requested': total_requested,
                'success_rate': total_selected / total_requested if total_requested > 0 else 0.0,
                'types_completed': [t for t in required_types if len(selected_places.get(t, [])) == selection_counts[t]],
                'types_partial': [t for t in required_types if 0 < len(selected_places.get(t, [])) < selection_counts[t]],
                'types_failed': [t for t in required_types if len(selected_places.get(t, [])) == 0]
            },
            'errors': errors  # 오류 목록 추가
        }

        return result
    
    def get_all_selected_places_flat(self, selection_result: Dict[str, Any]) -> List[Any]:
        """
        선택 결과에서 모든 장소들을 평면 리스트로 반환
        
        Args:
            selection_result: select_places_by_location 결과
            
        Returns:
            List: 모든 선택된 장소들의 리스트
        """
        all_places = []
        selected_places = selection_result.get('selected_places', {})
        
        for place_type, places in selected_places.items():
            all_places.extend(places)
        
        return all_places
    
    def convert_to_tripscheduler_format(self, selection_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        선택된 장소들을 TripScheduler 포맷으로 변환

        Args:
            selection_result: select_places_by_location 결과

        Returns:
            List[Dict]: TripScheduler 포맷의 장소 리스트
        """
        all_places = self.get_all_selected_places_flat(selection_result)
        tripscheduler_data = []

        for place in all_places:
            try:
                ts_format = place.to_tripscheduler_format()
                tripscheduler_data.append(ts_format)
            except Exception as e:
                print(f"[ERROR] {place.name} TripScheduler 포맷 변환 실패: {e}")
                continue

        return tripscheduler_data

    def validate_critical_places(self, selection_result: Dict[str, Any], day_type: str = None) -> Dict[str, Any]:
        """
        중요 장소 타입이 충분히 선택되었는지 검증

        Args:
            selection_result: select_places_by_location 결과
            day_type: 'first_day', 'middle_day', 'last_day', 'one_day_trip'

        Returns:
            Dict: 검증 결과 {'is_valid': bool, 'errors': list, 'warnings': list}
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        selected_places = selection_result.get('selected_places', {})
        selection_details = selection_result.get('selection_details', {})

        # 일정 타입별 필수 요구사항 정의
        critical_requirements = {
            'first_day': {'restaurant': 1, 'hotel': 0},  # 1일 여행이면 hotel=0
            'middle_day': {'restaurant': 1, 'hotel': 1},
            'last_day': {'restaurant': 1},
            'one_day_trip': {'restaurant': 1}
        }

        if day_type and day_type in critical_requirements:
            requirements = critical_requirements[day_type]
            for place_type, min_count in requirements.items():
                actual_count = len(selected_places.get(place_type, []))
                if actual_count < min_count:
                    error_msg = f"{day_type}에 필수인 {place_type} 타입 장소가 부족합니다 (필요: {min_count}개, 실제: {actual_count}개)"
                    validation_result['errors'].append({
                        'type': 'CRITICAL_PLACE_MISSING',
                        'day_type': day_type,
                        'place_type': place_type,
                        'required': min_count,
                        'actual': actual_count,
                        'message': error_msg
                    })
                    validation_result['is_valid'] = False
                    print(f"[VALIDATION ERROR] {error_msg}")

        # 일반 경고 - 요청한 개수보다 적게 선택된 경우
        for place_type, details in selection_details.items():
            requested = details.get('requested_count', 0)
            selected = details.get('selected_count', 0)
            if selected < requested and selected > 0:
                warning_msg = f"{place_type} 타입 장소가 요청보다 적게 선택되었습니다 (요청: {requested}개, 선택: {selected}개)"
                validation_result['warnings'].append({
                    'type': 'PARTIAL_SELECTION',
                    'place_type': place_type,
                    'requested': requested,
                    'selected': selected,
                    'message': warning_msg
                })

        return validation_result

# 편의를 위한 전역 선택기 인스턴스
default_selector = PlaceSelector()

def select_places(
    location_code: int,
    restaurant_count: int = 2,
    tour_count: int = 1,
    cafe_count: int = 0,
    hotel_count: int = 0,
    reference_hashtags: Optional[List[str]] = None,
    scoring_config: Optional[ScoringConfig] = None,
    reference_coords: Optional[Tuple[float, float]] = None
) -> Dict[str, Any]:
    """
    지역별 상위 점수 장소 선택 - 편의 함수

    Args:
        location_code: 지역 코드
        restaurant_count: 선택할 레스토랑 개수
        tour_count: 선택할 관광지 개수
        cafe_count: 선택할 카페 개수
        hotel_count: 선택할 호텔 개수
        reference_hashtags: 참조 해시태그들
        scoring_config: 점수 계산 설정
        reference_coords: 참조 좌표 (y_cord, x_cord) = (lat, lon)

    Returns:
        Dict: 선택 결과
    """
    config = SelectionConfig(
        restaurant_count=restaurant_count,
        tour_count=tour_count,
        cafe_count=cafe_count,
        hotel_count=hotel_count,
        reference_hashtags=reference_hashtags or [],
        scoring_config=scoring_config,
        reference_coords=reference_coords
    )

    return default_selector.select_places_by_location(location_code, config)


# 일자별 선택 함수들 추가
def select_places_for_first_day(
    location_code: int,
    reference_hashtags: Optional[List[str]] = None,
    scoring_config: Optional[ScoringConfig] = None,
    total_days: int = 3,
    reference_coords: Optional[Tuple[float, float]] = None
) -> Dict[str, Any]:
    """
    첫날 장소 선택: 숙소 1개, 관광지 2개, 식당 2개 (점심+저녁) (1일 여행인 경우 숙소 제외)

    Args:
        location_code: 지역 코드
        reference_hashtags: 참조 해시태그들
        scoring_config: 점수 계산 설정
        total_days: 총 여행 일수
        reference_coords: 참조 좌표 (y_cord, x_cord) = (lat, lon)

    Returns:
        Dict: 선택 결과
    """
    # 첫날 선택 - 1일 여행인 경우 숙소 제외
    hotel_count = 0 if total_days == 1 else 1

    return select_places(
        location_code=location_code,
        restaurant_count=2,
        tour_count=1,
        cafe_count=1,
        hotel_count=hotel_count,
        reference_hashtags=reference_hashtags,
        scoring_config=scoring_config,
        reference_coords=reference_coords
    )

def select_places_for_middle_day(
    location_code: int,
    reference_hashtags: Optional[List[str]] = None,
    scoring_config: Optional[ScoringConfig] = None
) -> Dict[str, Any]:
    """
    중간날 장소 선택: 숙소 1개, 관광지 1개, 식당 2개, 카페 1개

    Args:
        location_code: 지역 코드
        reference_hashtags: 참조 해시태그들
        scoring_config: 점수 계산 설정

    Returns:
        Dict: 선택 결과
    """
    # 중간날 선택
    return select_places(
        location_code=location_code,
        restaurant_count=2,
        tour_count=1,
        cafe_count=1,
        hotel_count=1,
        reference_hashtags=reference_hashtags,
        scoring_config=scoring_config
    )

def select_places_for_last_day(
    location_code: int,
    reference_hashtags: Optional[List[str]] = None,
    scoring_config: Optional[ScoringConfig] = None
) -> Dict[str, Any]:
    """
    마지막날 장소 선택: 식당 1개, 관광지 1개 (숙소 없음)
    
    Args:
        location_code: 지역 코드
        reference_hashtags: 참조 해시태그들
        scoring_config: 점수 계산 설정
        
    Returns:
        Dict: 선택 결과
    """
    # 마지막날 선택
    return select_places(
        location_code=location_code,
        restaurant_count=1,
        tour_count=1,
        cafe_count=1,
        hotel_count=0,
        reference_hashtags=reference_hashtags,
        scoring_config=scoring_config
    )

def select_places_for_day(
    day_number: int,
    total_days: int,
    location_code: int,
    reference_hashtags: Optional[List[str]] = None,
    scoring_config: Optional[ScoringConfig] = None
) -> Dict[str, Any]:
    """
    일자별 장소 선택 (자동으로 첫날/중간날/마지막날 구분)
    
    Args:
        day_number: 일차 (1부터 시작)
        total_days: 총 여행 일수
        location_code: 지역 코드
        reference_hashtags: 참조 해시태그들
        scoring_config: 점수 계산 설정
        
    Returns:
        Dict: 선택 결과
    """
    if day_number == 1:
        # 첫날
        return select_places_for_first_day(location_code, reference_hashtags, scoring_config, total_days)
    elif day_number == total_days:
        # 마지막날
        return select_places_for_last_day(location_code, reference_hashtags, scoring_config)
    else:
        # 중간날
        return select_places_for_middle_day(location_code, reference_hashtags, scoring_config)