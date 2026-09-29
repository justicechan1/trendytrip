import json
from typing import Dict, Any, Optional
from tripscheduler.cli.utils import (
    generate_valid_combinations,
    build_selection_inputs
)
from tripscheduler.core.preprocessing.timewindow import calculate_effective_time_windows
from tripscheduler.core.preprocessing.restaurant import split_restaurant_nodes
from tripscheduler.scheduler import run_scheduler

def schedule_trip(
    data: Dict[str, Any],
    use_mock: bool = False,
    mock_raw_path: Optional[str] = None,
    output_path: Optional[str] = None,
    time_limit_sec: int = 20,
    window_slack: int = 30
) -> Dict[str, Any]:
    """
    외부에서 사용할 수 있는 파이프라인 wrapper.
    - data: tc.json 형태의 dict
    - output_path: 저장할 파일 경로 (예: "results.json")
    - return: results.json의 dict 형태
    """

    places, user, day_info = data["places"], data["user"], data["day_info"]

    # 1. 시간 윈도우 계산
    eff_windows_map = calculate_effective_time_windows(places, user)

    # 2. 식당 노드 분리
    new_places, new_windows = split_restaurant_nodes(places, eff_windows_map)

    # 3. 유효한 조합 생성
    valid_selections = generate_valid_combinations(new_places, new_windows)
    print(f"[SCHEDULER_API] Valid combinations: {len(valid_selections)}")
    if not valid_selections:
        print(f"[SCHEDULER_API] No valid combinations found!")
        print(f"[SCHEDULER_API] Places: {[p['name'] for p in new_places]}")
        print(f"[SCHEDULER_API] Windows: {new_windows}")

    # 4. 조합별 스케줄링 실행
    results = {}
    for sel in valid_selections:
        print(f"[SCHEDULER_API] Testing combination: {sel}")
        sel_places, sel_windows, labels = build_selection_inputs(new_places, new_windows, sel)

        try:
            visits, cost, full_path = run_scheduler(
                sel_places,
                sel_windows,
                user,
                day_info,
                use_mock=use_mock,
                mock_raw_path=mock_raw_path,
                time_limit_sec=time_limit_sec,
                window_slack=window_slack
            )
            print(f"[SCHEDULER_API] Scheduler succeeded: {len(visits)} visits, {len(full_path)} path segments")
            results[sel] = {
                "cost": cost,
                "visits": visits,
                "path": full_path
            }
        except Exception as e:
            print(f"[SCHEDULER_API] Scheduler failed: {e}")
            import traceback
            print(f"[SCHEDULER_API] Traceback: {traceback.format_exc()}")
            results[sel] = None

    # 5. 결과 저장 (최고 결과 or 첫 번째 결과)
    first_value = next((v for v in results.values() if v), None)

    if first_value and isinstance(first_value, dict):
        output_data = {
            "visits": first_value.get("visits", []),
            "path": first_value.get("path", [])
        }
    else:
        # 결과가 없거나 잘못된 형식인 경우 빈 결과 반환
        output_data = {
            "visits": [],
            "path": []
        }


    return output_data
