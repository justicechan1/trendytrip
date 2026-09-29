"""
TripPlanner 래핑 함수
"""
import sys
import os
from typing import Dict, Any

# TripRecommendationSystem src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from src.trip_planner import TripPlanner


def validate_input_data(input_data: Dict[str, Any]) -> bool:
    """입력 데이터 검증"""
    required_fields = ['total_days', 'start_time', 'end_time', 'daily_locations', 'start_date']
    
    for field in required_fields:
        if field not in input_data:
            return False
    
    if not isinstance(input_data['total_days'], int) or input_data['total_days'] <= 0:
        return False
        
    if not isinstance(input_data['daily_locations'], list):
        return False
        
    if len(input_data['daily_locations']) != input_data['total_days']:
        return False
        
    return True


def plan_trip(input_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
    """
    여행 계획을 생성합니다.

    Args:
        input_data: 여행 계획 입력 데이터 (basic_3day_jeju.json과 같은 형태)
        use_mock: Mock 모드 사용 여부 (기본값: False)

    Returns:
        Dict: 여행 계획 결과 (raw format)
    """
    # 입력 데이터 검증
    if not validate_input_data(input_data):
        return {
            'success': False,
            'error': 'Invalid input data format',
            'day_results': []
        }

    try:
        planner = TripPlanner(silent=True)
        result = planner.plan_trip(input_data, use_mock=use_mock)
        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'day_results': []
        }