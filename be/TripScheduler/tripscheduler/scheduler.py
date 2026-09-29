from tripscheduler.core.indexing.handlers import determine_start_end_indices
from tripscheduler.core.routing.components import (
    create_routing_model,
    register_transit,
    add_disjunctions,
    add_time_constraints,
    get_default_search_parameters
)
from tripscheduler.core.routing.dummy import add_dummy_node
from tripscheduler.core.routing.context import build_context
from tripscheduler.core.routing.parser import parse_solution
from tripscheduler.api.prepare import prepare_matrices
from tripscheduler.utils.time import time_to_minutes

import os
from dotenv import load_dotenv

load_dotenv()

def run_scheduler(
    places,
    windows,
    user,
    day_info,
    use_mock: bool,
    mock_raw_path: str = None,
    time_limit_sec: int = 20,
    window_slack: int = 30
):
    # 1) API 키 로드
    api_key_id = os.environ.get("NAVER_API_CLIENT_ID")
    api_key    = os.environ.get("NAVER_API_CLIENT_SECRET")

    # 2) 스냅 & 매트릭스 생성 (time_matrix, raw 응답)
    time_matrix, raw, path_matrix = prepare_matrices(
        places, api_key_id, api_key,
        use_mock=use_mock,
        mock_raw_path=mock_raw_path
    )

    # 3) 시작/종료 노드 결정
    start_idx, end_idx = determine_start_end_indices(places, day_info)

    # 4) 글로벌 시간 범위 계산
    gs = time_to_minutes(user["start_time"])
    ge = time_to_minutes(user["end_time"])

    # 5) 더미 노드 추가 (필요 시)
    if start_idx is None:
        start_idx = add_dummy_node(places, windows, "start", gs, ge)
    if end_idx is None:
        end_idx = add_dummy_node(places, windows, "end", gs, ge)

    # 6) 서비스 시간 리스트
    svc_times = [p.get("service_time", 0) for p in places]

    # 7) OR-Tools 모델 빌드
    n = len(places)
    mgr, routing = create_routing_model(n, start_idx, end_idx)
    transit_cb = register_transit(routing, mgr, time_matrix, svc_times, places)
    add_disjunctions(routing, mgr, places, start_idx, end_idx)
    time_dim = add_time_constraints(
        routing, transit_cb, gs, ge, windows, mgr, start_idx, end_idx, window_slack
    )

    # 8) 파라미터 설정 후 Solve
    params   = get_default_search_parameters(time_limit_sec)
    solution = routing.SolveWithParameters(params)

    # 9) 결과 파싱 & 경로 추출
    if solution:

        ctx = build_context(
            places, windows, time_matrix, svc_times,
            start_idx, end_idx, gs, ge,
            routing, mgr, transit_cb, time_dim,
            path_matrix=path_matrix
        )
        visits, full_path = parse_solution(ctx, solution)
        objective = solution.ObjectiveValue()
        return visits, objective, full_path

    return [], None, []