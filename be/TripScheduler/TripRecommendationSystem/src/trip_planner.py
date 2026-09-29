import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

import json
import argparse
import copy
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from selection.place_selector import select_places_for_first_day, select_places_for_middle_day, select_places_for_last_day
from database.unified_queries import get_transport_by_id

# Add tripscheduler to path for scheduler_api import
tripscheduler_path = Path(__file__).parent.parent.parent / 'tripscheduler'
sys.path.insert(0, str(tripscheduler_path))
from scheduler_api import schedule_trip
from tripscheduler.utils.time import time_to_minutes

class TripPlanner:
    """여행 계획 시스템"""
    
    def __init__(self, silent: bool = True):
        self.silent = silent
        self.results = {
            'success': False,
            'day_results': [],
            'error': None
        }
    
    def plan_trip(self, input_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """여행 계획 생성"""

        try:
            self.results = {
                'success': False,
                'day_results': [],
                'error': None
            }

            # 각 날짜별 순차 처리
            for day_number in range(1, input_data['total_days'] + 1):
                day_result = self.process_single_day(day_number, input_data, use_mock)
                self.results['day_results'].append(day_result)
                
                if not day_result['success']:
                    self.results['error'] = f"Day {day_number} failed: {day_result.get('error')}"
                    return self.results
            
            # 모든 날짜가 성공하면 전체 성공
            if len(self.results['day_results']) == input_data['total_days'] and all(d['success'] for d in self.results['day_results']):
                self.results['success'] = True
            
            return self.results
            
        except Exception as e:
            self.results['error'] = str(e)
            return self.results
    
    def process_single_day(self, day_number: int, input_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """단일 날짜 처리"""

        location_code = input_data['daily_locations'][day_number - 1]
        date = (datetime.strptime(input_data["start_date"], '%Y-%m-%d') + timedelta(days=day_number-1)).strftime('%Y-%m-%d')

        day_result = {
            'day_number': day_number,
            'date': date,
            'location_code': location_code,
            'success': False,
            'visits': [],
            'path': [],
            'error': None
        }

        try:
            # 1. 장소 선택
            if day_number == 1:
                places_result = self.process_first_day(location_code, input_data)
            elif day_number == input_data['total_days']:
                places_result = self.process_last_day(location_code, input_data)
            else:
                places_result = self.process_middle_day(location_code, input_data)

            if not places_result:
                day_result['error'] = "Place selection failed"
                return day_result

            # 1-1. 장소 선택 오류 정보 저장
            day_result['selection_errors'] = places_result.get('selection_errors', [])
            day_result['selection_summary'] = places_result.get('selection_summary', {})

            # 2. TripScheduler 실행 (재시도 로직 포함)
            scheduler_result = self.execute_tripscheduler_with_retry(places_result, day_number, input_data, use_mock)

            if scheduler_result['success']:
                day_result['success'] = True
                day_result['visits'] = scheduler_result['visits']
                day_result['path'] = scheduler_result.get('path', [])
                day_result['retry_history'] = scheduler_result.get('retry_history', [])
            else:
                day_result['error'] = scheduler_result['error']
                day_result['retry_history'] = scheduler_result.get('retry_history', [])

            return day_result
            
        except Exception as e:
            day_result['error'] = str(e)
            return day_result
    
    def process_first_day(self, location_code: int, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """첫째날 처리"""

        # 1. 시작 교통편 조회
        start_transport = get_transport_by_id(input_data.get('start_transport_id', 1))
        if not start_transport:
            print("[TRIP_PLANNER ERROR] 시작 교통편을 찾을 수 없습니다")
            return None

        # 2. 첫째날 장소 선택
        places = select_places_for_first_day(
            location_code=location_code,
            reference_hashtags=input_data.get('hashtags'),
            total_days=input_data['total_days']
        )

        # 2-1. 장소 선택 오류 체크
        selection_errors = places.get('errors', [])
        if selection_errors:
            for error in selection_errors:
                print(f"[TRIP_PLANNER WARNING] 장소 선택 경고: {error['message']}")

        selected_places = places['selected_places']
        
        # 3. TripScheduler 입력 형식 생성
        all_places = []
        
        # 시작 교통편 추가
        transport_data = start_transport.to_tripscheduler_format()
        transport_data['service_time'] = 0
        transport_data['is_mandatory'] = True
        transport_data['tags'] = transport_data.get('tags', []) + ['시작점']
        all_places.append(transport_data)
        
        # 선택된 장소들 추가
        for place_type, place_list in selected_places.items():
            for place in place_list:
                try:
                    place_data = place.to_tripscheduler_format()
                    all_places.append(place_data)
                except Exception:
                    continue

        # 당일치기인 경우 종료 교통편 추가
        if input_data['total_days'] == 1:
            end_transport = get_transport_by_id(input_data.get('end_transport_id', 1))
            if end_transport:
                end_transport_data = end_transport.to_tripscheduler_format()
                end_transport_data['service_time'] = 0
                end_transport_data['is_mandatory'] = True
                end_transport_data['tags'] = end_transport_data.get('tags', []) + ['종료지점']
                all_places.append(end_transport_data)

        date = input_data["start_date"]

        return {
            'places': all_places,
            'user': {
                'start_time': input_data['start_time'],
                'end_time': input_data['end_time'],
                'travel_style': 'relaxed',
                'meal_time_preferences': {
                    'breakfast': ['08:00', '09:00'],
                    'lunch': ['12:00', '13:00'],
                    'dinner': ['18:00', '19:00']
                }
            },
            'day_info': {
                'is_first_day': True,
                'is_last_day': input_data['total_days'] == 1,
                'date': date,
                'weekday': datetime.strptime(date, '%Y-%m-%d').strftime('%A')
            },
            'selection_errors': selection_errors,  # 장소 선택 오류 정보 추가
            'selection_summary': places.get('summary', {})
        }
    
    def process_middle_day(self, location_code: int, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """중간날 처리"""
        
        # 1. 전날 마지막 위치 찾기
        prev_day_visits = self.results['day_results'][-1]['visits']
        if not prev_day_visits:
            return None
        
        last_visit = prev_day_visits[-1]
        
        # 2. 시작 위치 생성
        start_location = {
            'id': last_visit.get('id', 999),
            'name': last_visit['place'],
            'x_cord': last_visit['x_cord'],
            'y_cord': last_visit['y_cord'],
            'category': 'accommodation',
            'open_time': '00:00',
            'close_time': '23:59',
            'service_time': 0,
            'tags': ['숙소', '시작점'],
            '휴무일': [],
            'break_time': [],
            'is_mandatory': True
        }
        
        # 3. 중간날 장소 선택
        places = select_places_for_middle_day(
            location_code=location_code,
            reference_hashtags=input_data.get('hashtags')
        )

        # 3-1. 장소 선택 오류 체크
        selection_errors = places.get('errors', [])
        if selection_errors:
            for error in selection_errors:
                print(f"[TRIP_PLANNER WARNING] 장소 선택 경고: {error['message']}")

        selected_places = places['selected_places']
        
        # 4. TripScheduler 입력 형식 생성
        all_places = [start_location]
        
        for place_type, place_list in selected_places.items():
            for place in place_list:
                try:
                    place_data = place.to_tripscheduler_format()
                    all_places.append(place_data)
                except Exception:
                    continue
        
        day_number = len(self.results['day_results']) + 1
        date = (datetime.strptime(input_data["start_date"], '%Y-%m-%d') + timedelta(days=day_number-1)).strftime('%Y-%m-%d')

        return {
            'places': all_places,
            'user': {
                'start_time': input_data['start_time'],
                'end_time': input_data['end_time'],
                'travel_style': 'relaxed',
                'meal_time_preferences': {
                    'breakfast': ['08:00', '09:00'],
                    'lunch': ['12:00', '13:00'],
                    'dinner': ['18:00', '19:00']
                }
            },
            'day_info': {
                'is_first_day': False,
                'is_last_day': day_number == input_data['total_days'],
                'date': date,
                'weekday': datetime.strptime(date, '%Y-%m-%d').strftime('%A')
            },
            'selection_errors': selection_errors,
            'selection_summary': places.get('summary', {})
        }
    
    def process_last_day(self, location_code: int, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """마지막날 처리"""
        
        # 1. 전날 마지막 위치 찾기
        prev_day_visits = self.results['day_results'][-1]['visits']
        if not prev_day_visits:
            return None
        
        last_visit = prev_day_visits[-1]
        
        # 2. 시작 위치 생성
        start_location = {
            'id': last_visit.get('id', 999),
            'name': last_visit['place'],
            'x_cord': last_visit['x_cord'],
            'y_cord': last_visit['y_cord'],
            'category': last_visit.get('category', 'accommodation'),
            'open_time': '00:00',
            'close_time': '23:59',
            'service_time': 0,
            'tags': ['시작점'],
            '휴무일': [],
            'break_time': [],
            'is_mandatory': True
        }
        
        # 3. 마지막날 장소 선택
        places = select_places_for_last_day(
            location_code=location_code,
            reference_hashtags=input_data.get('hashtags')
        )

        # 3-1. 장소 선택 오류 체크
        selection_errors = places.get('errors', [])
        if selection_errors:
            for error in selection_errors:
                print(f"[TRIP_PLANNER WARNING] 장소 선택 경고: {error['message']}")

        selected_places = places['selected_places']
        
        # 4. 종료 교통편 조회
        end_transport = get_transport_by_id(input_data.get('end_transport_id', 1))
        
        # 5. TripScheduler 입력 형식 생성
        all_places = [start_location]
        
        for place_type, place_list in selected_places.items():
            for place in place_list:
                try:
                    place_data = place.to_tripscheduler_format()
                    all_places.append(place_data)
                except Exception:
                    continue
        
        # 종료 교통편 추가
        if end_transport:
            try:
                transport_data = end_transport.to_tripscheduler_format()
                transport_data['is_mandatory'] = True
                transport_data['tags'] = transport_data.get('tags', []) + ['종료지점']
                all_places.append(transport_data)
            except Exception:
                pass
        
        day_number = len(self.results['day_results']) + 1
        date = (datetime.strptime(input_data["start_date"], '%Y-%m-%d') + timedelta(days=day_number-1)).strftime('%Y-%m-%d')

        return {
            'places': all_places,
            'user': {
                'start_time': input_data['start_time'],
                'end_time': input_data['end_time'],
                'travel_style': 'relaxed',
                'meal_time_preferences': {
                    'breakfast': ['08:00', '09:00'],
                    'lunch': ['12:00', '13:00'],
                    'dinner': ['18:00', '19:00']
                }
            },
            'day_info': {
                'is_first_day': False,
                'is_last_day': True,
                'date': date,
                'weekday': datetime.strptime(date, '%Y-%m-%d').strftime('%A')
            },
            'selection_errors': selection_errors,
            'selection_summary': places.get('summary', {})
        }
    
    def _execute_simple_tripscheduler(self, places_data: Dict[str, Any], use_mock: bool = False,
                                      time_limit_sec: int = 10, window_slack: int = 10) -> Dict[str, Any]:
        """특정 날짜에 대해 scheduler_api 실행"""

        try:
            # scheduler_api의 schedule_trip 함수를 직접 호출
            result = schedule_trip(places_data, use_mock=use_mock,
                                 time_limit_sec=time_limit_sec,
                                 window_slack=window_slack)

            # scheduler_api 결과를 그대로 반환
            if result and result.get("visits"):
                return {
                    'success': True,
                    'visits': result["visits"],
                    'path': result.get("path", [])
                }
            else:
                return {'success': False, 'error': "No schedule generated"}

        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    
    def execute_tripscheduler_with_retry(self, places_data: Dict[str, Any], day_number: int, input_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """재시도 로직이 포함된 TripScheduler 실행 (점진적 제약 완화)"""

        retry_history = []  # 재시도 이력 추적

        # 1차 시도: 기본 제약 (time_limit=20초, window_slack=30분)
        result = self._execute_simple_tripscheduler(places_data, use_mock,
                                                    time_limit_sec=20, window_slack=30)
        retry_history.append({
            'attempt': 1,
            'time_limit': 20,
            'window_slack': 30,
            'success': result['success'],
            'error': result.get('error') if not result['success'] else None
        })
        if result['success']:
            result['retry_history'] = retry_history
            return result

        print(f"[TRIP_PLANNER] 1차 시도 실패: {result.get('error')}. 제약 완화 재시도 시작...")

        # 2차 시도: 제약 약간 완화 (time_limit=30초, window_slack=60분)
        print(f"[TRIP_PLANNER] 2차 시도 - 제약 완화 (time_limit=30초, window_slack=60분)")
        result = self._execute_simple_tripscheduler(places_data, use_mock,
                                                    time_limit_sec=30, window_slack=60)
        retry_history.append({
            'attempt': 2,
            'time_limit': 30,
            'window_slack': 60,
            'success': result['success'],
            'error': result.get('error') if not result['success'] else None
        })
        if result['success']:
            result['retry_history'] = retry_history
            return result

        # 3차 시도: 제약 더 완화 (time_limit=40초, window_slack=90분)
        print(f"[TRIP_PLANNER] 3차 시도 - 제약 더 완화 (time_limit=40초, window_slack=90분)")
        result = self._execute_simple_tripscheduler(places_data, use_mock,
                                                    time_limit_sec=40, window_slack=90)
        retry_history.append({
            'attempt': 3,
            'time_limit': 40,
            'window_slack': 90,
            'success': result['success'],
            'error': result.get('error') if not result['success'] else None
        })
        if result['success']:
            result['retry_history'] = retry_history
            return result

        # 4차 시도: 장소 조정과 함께 제약 완화
        print(f"[TRIP_PLANNER] 4차 시도 - 장소 조정 + 제약 최대 완화")
        result = self._retry_with_adjusted_places(places_data, day_number, input_data, use_mock)
        result['retry_history'] = retry_history + result.get('retry_history', [])
        return result
    
    def _retry_with_adjusted_places(self, original_places_data: Dict[str, Any], day_number: int, input_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """장소 조정을 통한 재시도 - 1차 교체, 2차부터 하나씩 제거"""

        retry_history = []

        # 제거 가능한 장소 수 계산 (최대 시도 횟수 결정)
        removable_count = sum(1 for p in original_places_data.get('places', []) if not p.get('is_mandatory', False))
        max_attempts = max(removable_count, 3)  # 최소 3번, 최대 제거 가능한 장소 수만큼

        print(f"[TRIP_PLANNER] 장소 조정 시작 (제거 가능 장소: {removable_count}개, 최대 시도: {max_attempts}번)")

        for attempt in range(1, max_attempts + 1):
            print(f"[TRIP_PLANNER] 재시도 {attempt}/{max_attempts} (장소 조정)")

            # 시도별 장소 조정
            adjusted_places_data = self._adjust_places_for_attempt(
                original_places_data, attempt, day_number, input_data
            )

            if not adjusted_places_data:
                print(f"[TRIP_PLANNER] 더 이상 조정할 장소 없음. 재시도 중단.")
                retry_history.append({
                    'attempt': 3 + attempt,
                    'strategy': 'place_adjustment',
                    'success': False,
                    'error': '조정할 장소 없음'
                })
                break

            # 조정된 장소로 TripScheduler 실행
            # slack을 순차적으로 늘림: 120분 → 180분 → 240분 → 300분 ...
            current_slack = 120 + (attempt - 1) * 60
            result = self._execute_simple_tripscheduler(adjusted_places_data, use_mock,
                                                       time_limit_sec=50, window_slack=current_slack)

            remaining_places = len(adjusted_places_data.get('places', []))
            retry_history.append({
                'attempt': 3 + attempt,
                'strategy': 'place_adjustment',
                'time_limit': 50,
                'window_slack': current_slack,
                'remaining_places': remaining_places,
                'success': result['success'],
                'error': result.get('error') if not result['success'] else None
            })

            if result['success']:
                print(f"[TRIP_PLANNER] 장소 조정 재시도 성공! (남은 장소: {remaining_places}개)")
                result['retry_history'] = retry_history
                return result
            else:
                print(f"[TRIP_PLANNER] 장소 조정 재시도 실패 (남은 장소: {remaining_places}개): {result.get('error')}")

        # 최종 안전장치 1: 최소 장소 + 극도로 관대한 제약
        print(f"[TRIP_PLANNER] 최종 안전장치 1 - 최소 장소로 시도")
        minimal_result = self._create_minimal_schedule(original_places_data, use_mock)
        retry_history.append({
            'attempt': 7,
            'strategy': 'minimal_schedule',
            'time_limit': 60,
            'window_slack': 180,
            'success': minimal_result['success'],
            'error': minimal_result.get('error') if not minimal_result['success'] else None
        })
        if minimal_result['success']:
            minimal_result['retry_history'] = retry_history
            return minimal_result

        # 최종 안전장치 2: 간단한 기본 일정 생성 (항상 성공)
        print(f"[TRIP_PLANNER] 최종 안전장치 2 - 기본 일정 생성")
        fallback_result = self._create_simple_fallback_schedule(original_places_data)
        retry_history.append({
            'attempt': 8,
            'strategy': 'simple_fallback',
            'success': True,
            'error': None
        })
        fallback_result['retry_history'] = retry_history
        return fallback_result
    
    def _adjust_places_for_attempt(self, places_data: Dict[str, Any], attempt: int, day_number: int, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """시도별 장소 조정 - 1차 교체, 2차부터 하나씩 제거"""

        if attempt == 1:
            # 1차: 장소 교체 시도
            result = self._replace_places(places_data, day_number, input_data)
            if result:
                return result
            # 교체 실패시 1개 제거로 대체
            print("[ADJUST] 장소 교체 실패, 1개 제거로 대체")
            return self._remove_farthest_places(places_data, remove_count=1)
        else:
            # 2차부터: 가장 먼 장소부터 하나씩 제거 (attempt 개 제거)
            return self._remove_farthest_places(places_data, remove_count=attempt)
    
    def _replace_places(self, places_data: Dict[str, Any], day_number: int, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """장소 교체 로직"""
        
        try:
            adjusted_data = copy.deepcopy(places_data)
            places = adjusted_data['places']
            
            # 필수 장소는 제외하고 교체 가능한 장소들 찾기
            replaceable_places = []
            for i, place in enumerate(places):
                if not place.get('is_mandatory', False):
                    replaceable_places.append(i)
            
            if not replaceable_places:
                return None
            
            # 추가 후보 장소들 가져오기
            location_code = input_data['daily_locations'][day_number - 1]
            alternative_places = self._get_alternative_places(location_code, day_number, input_data)
            
            if not alternative_places:
                return None
            
            # 랜덤하게 1-2개 장소 교체
            replace_count = min(len(replaceable_places), len(alternative_places), 2)
            places_to_replace = random.sample(replaceable_places, replace_count)
            
            for i, place_idx in enumerate(places_to_replace):
                if i < len(alternative_places):
                    places[place_idx] = alternative_places[i]
            
            return adjusted_data
            
        except Exception as e:
            if not self.silent:
                print(f"장소 교체 중 오류: {e}")
            return None
    
    def _remove_some_places(self, places_data: Dict[str, Any], remove_count: int = 1) -> Optional[Dict[str, Any]]:
        """일부 장소 제거 로직"""
        
        try:
            adjusted_data = copy.deepcopy(places_data)
            places = adjusted_data['places']
            
            # 필수가 아닌 장소들 찾기
            removable_places = []
            for i, place in enumerate(places):
                if not place.get('is_mandatory', False):
                    removable_places.append(i)
            
            if len(removable_places) <= remove_count:
                # 제거 가능한 장소가 너무 적음
                return None
            
            # 랜덤하게 장소 제거
            places_to_remove = random.sample(removable_places, min(remove_count, len(removable_places)))
            
            # 인덱스 순서대로 정렬해서 뒤에서부터 제거 (인덱스 변경 방지)
            for place_idx in sorted(places_to_remove, reverse=True):
                places.pop(place_idx)
            
            return adjusted_data
            
        except Exception as e:
            if not self.silent:
                print(f"장소 제거 중 오류: {e}")
            return None

    def _remove_farthest_places(self, places_data: Dict[str, Any], remove_count: int = 1) -> Optional[Dict[str, Any]]:
        """시작/종료 노드에서 가장 먼 장소부터 제거"""

        try:
            adjusted_data = copy.deepcopy(places_data)
            places = adjusted_data['places']

            # 시작/종료 노드 찾기 (is_mandatory=True인 transport)
            start_node = None
            for place in places:
                if place.get('is_mandatory', False) and place.get('category') == 'transport':
                    start_node = place
                    break

            if not start_node:
                # 시작 노드를 못 찾으면 첫 번째 장소를 기준으로
                start_node = places[0] if places else None

            if not start_node:
                return None

            start_x = start_node.get('x_cord', 0)
            start_y = start_node.get('y_cord', 0)

            # 필수가 아닌 장소들의 거리 계산
            removable_with_distance = []
            for i, place in enumerate(places):
                if not place.get('is_mandatory', False):
                    px = place.get('x_cord', 0)
                    py = place.get('y_cord', 0)
                    # 간단한 유클리드 거리 (정확한 거리 계산은 불필요)
                    dist = ((px - start_x) ** 2 + (py - start_y) ** 2) ** 0.5
                    removable_with_distance.append((i, dist, place.get('name', '?')))

            # 제거 가능한 장소가 최소 1개는 남아야 함
            if len(removable_with_distance) <= remove_count:
                print(f"[ADJUST] 제거 가능한 장소 부족: {len(removable_with_distance)}개, 제거 요청: {remove_count}개")
                return None

            # 거리순 정렬 (먼 것부터)
            removable_with_distance.sort(key=lambda x: x[1], reverse=True)

            # 가장 먼 장소들 제거
            places_to_remove = [item[0] for item in removable_with_distance[:remove_count]]
            removed_names = [item[2] for item in removable_with_distance[:remove_count]]

            print(f"[ADJUST] 가장 먼 장소 {remove_count}개 제거: {removed_names}")

            # 인덱스 역순으로 제거
            for place_idx in sorted(places_to_remove, reverse=True):
                places.pop(place_idx)

            print(f"[ADJUST] 남은 장소 수: {len(places)}개")
            return adjusted_data

        except Exception as e:
            print(f"[ADJUST] 장소 제거 중 오류: {e}")
            return None

    def _get_alternative_places(self, location_code: int, day_number: int, input_data: Dict[str, Any]) -> list:
        """대체 장소들 가져오기"""
        
        try:
            # 현재 날짜 타입에 따라 추가 장소 선택
            if day_number == 1:
                places = select_places_for_first_day(
                    location_code=location_code,
                    reference_hashtags=input_data.get('hashtags'),
                    total_days=input_data['total_days']
                )
            elif day_number == input_data['total_days']:
                places = select_places_for_last_day(
                    location_code=location_code,
                    reference_hashtags=input_data.get('hashtags')
                )
            else:
                places = select_places_for_middle_day(
                    location_code=location_code,
                    reference_hashtags=input_data.get('hashtags')
                )
            
            # 추가 후보들을 TripScheduler 형식으로 변환
            alternatives = []
            selected_places = places['selected_places']
            
            for place_type, place_list in selected_places.items():
                # 각 타입별로 2-3개씩 추가 후보 확보
                for place in place_list[2:5]:  # 처음 2개는 건너뛰고 3-5번째 사용
                    try:
                        place_data = place.to_tripscheduler_format()
                        alternatives.append(place_data)
                    except Exception:
                        continue
            
            return alternatives[:3]  # 최대 3개까지
            
        except Exception as e:
            if not self.silent:
                print(f"대체 장소 조회 중 오류: {e}")
            return []

    def _create_minimal_schedule(self, original_places_data: Dict[str, Any], use_mock: bool = False) -> Dict[str, Any]:
        """최소 장소만으로 일정 생성 (극도로 관대한 제약)"""

        try:
            adjusted_data = copy.deepcopy(original_places_data)
            places = adjusted_data['places']

            # 필수 장소만 남기기 + 식당 1개
            minimal_places = []
            restaurant_added = False

            for place in places:
                # 필수 장소는 모두 유지
                if place.get('is_mandatory', False):
                    minimal_places.append(place)
                # 식당 1개만 추가
                elif place.get('category') == 'restaurant' and not restaurant_added:
                    minimal_places.append(place)
                    restaurant_added = True

            # 최소 3개 이상 장소가 있어야 함
            if len(minimal_places) < 3:
                # 추가 장소 넣기
                for place in places:
                    if place not in minimal_places:
                        minimal_places.append(place)
                        if len(minimal_places) >= 3:
                            break

            adjusted_data['places'] = minimal_places

            if not self.silent:
                print(f"최소 장소 {len(minimal_places)}개로 시도")

            # 극도로 관대한 제약: time_limit=60초, window_slack=180분(3시간)
            result = self._execute_simple_tripscheduler(adjusted_data, use_mock,
                                                       time_limit_sec=60, window_slack=180)
            return result

        except Exception as e:
            if not self.silent:
                print(f"최소 장소 일정 생성 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _create_simple_fallback_schedule(self, original_places_data: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 기본 일정 생성 (항상 성공)"""

        try:
            places = original_places_data['places']
            user = original_places_data['user']

            # 시작/종료 시간 파싱
            start_time = time_to_minutes(user['start_time'])
            end_time = time_to_minutes(user['end_time'])

            # 필수 장소 필터링
            mandatory_places = [p for p in places if p.get('is_mandatory', False)]
            optional_places = [p for p in places if not p.get('is_mandatory', False)]

            # 최대 5개 장소 선택 (필수 + 선택 일부)
            selected_places = mandatory_places + optional_places[:max(0, 5 - len(mandatory_places))]

            # 시간을 균등 배분
            total_time = end_time - start_time
            if len(selected_places) <= 1:
                time_per_place = total_time
            else:
                time_per_place = total_time // len(selected_places)

            visits = []
            current_time = start_time

            for idx, place in enumerate(selected_places):
                service_time = place.get('service_time', 60)

                # 마지막 장소는 종료 시간에 맞춤
                if idx == len(selected_places) - 1:
                    arrival = min(current_time, end_time - service_time)
                    departure = end_time
                else:
                    arrival = current_time
                    departure = min(current_time + service_time, end_time)

                visits.append({
                    'order': idx + 1,
                    'place': place['name'],
                    'id': place.get('id'),
                    'arrival_str': f"{arrival // 60:02d}:{arrival % 60:02d}",
                    'departure_str': f"{departure // 60:02d}:{departure % 60:02d}",
                    'x_cord': place['x_cord'],
                    'y_cord': place['y_cord'],
                    'category': place.get('category', 'unknown')
                })

                current_time = departure + 30  # 이동시간 30분 가정

            if not self.silent:
                print(f"기본 일정 생성 완료: {len(visits)}개 방문지")

            return {
                'success': True,
                'visits': visits,
                'path': []
            }

        except Exception as e:
            if not self.silent:
                print(f"기본 일정 생성 실패 (치명적): {e}")
            # 최악의 경우: 빈 일정이라도 반환
            return {
                'success': True,
                'visits': [],
                'path': []
            }


def plan_trip_from_file(input_file_path: str, output_file_path: Optional[str] = None) -> Dict[str, Any]:
    """파일에서 입력을 받아 여행 계획 생성"""
    
    try:
        # 입력 파일 로드
        with open(input_file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        # 여행 계획 생성
        planner = TripPlanner(silent=True)
        result = planner.plan_trip(input_data)
        
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'day_results': [],
            'error': str(e)
        }


def main():
    """CLI 인터페이스"""
    parser = argparse.ArgumentParser(description='Trip Planner - Generate travel itinerary')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('-o', '--output', help='Output JSON file path (optional)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    # 여행 계획 생성
    result = plan_trip_from_file(args.input_file, args.output)
    
    # 결과 출력
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()