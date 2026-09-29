import json
from typing import Optional, Tuple, List, Dict

from tripscheduler.api.snap       import snap_to_road
from tripscheduler.api.directions import create_matrices
from tripscheduler.api.mock       import create_distance_matrix

def prepare_matrices(
    places: List[Dict],
    api_key_id: str,
    api_key: str,
    use_mock: bool = False,
    mock_raw_path: Optional[str] = None,
) -> Tuple[List[List[int]], List[List[Dict]], List[List[Optional[List[float]]]]]:
    """
    장소 리스트를 받아:
      - time_matrix, raw, path_matrix를 반환.
      - use_mock+mock_raw_path 있으면 mock으로,
      - use_mock만 있으면 하버사인 mock,
      - 아니면 실제 API (스냅→directions)
    """
    # DEBUG: use_mock 값 확인
    print(f"[DEBUG PREPARE_MATRICES] use_mock={use_mock}, mock_raw_path={mock_raw_path}, places_count={len(places)}")

    # 1) mock + raw 데이터
    if use_mock and mock_raw_path:
        with open(mock_raw_path, 'r', encoding='utf-8') as f:
            mock_response_matrix = json.load(f)
        return create_matrices(
            places, api_key_id, api_key,
            is_mock_enabled=True, mock_api_response=mock_response_matrix
        )

    # 2) mock only
    if use_mock:
        print(f"[DEBUG PREPARE_MATRICES] Using mock mode (Haversine distances)")
        duration_matrix = create_distance_matrix(places)
        n = len(places)
        raw_api_response = [[None] * n for _ in range(n)]
        path_matrix = [[None] * n for _ in range(n)]

        # Mock 모드에서도 간단한 직선 경로 생성 (시작점 -> 끝점)
        for i in range(n):
            for j in range(n):
                if i != j:
                    # 두 지점을 연결하는 직선 경로 (시작점, 끝점)
                    path_matrix[i][j] = [
                        [places[i]['x_cord'], places[i]['y_cord']],
                        [places[j]['x_cord'], places[j]['y_cord']]
                    ]

        return duration_matrix, raw_api_response, path_matrix

    # 3) 실제 API: 좌표 스냅 후 matrix 생성 snap 이 필요한가? 나중에 고민
    print(f"[DEBUG PREPARE_MATRICES] Using REAL API mode (calling Naver Directions)")
    # for p in places:
    #     p['y_cord'], p['x_cord'] = snap_to_road(
    #         p['y_cord'], p['x_cord'],
    #         api_key_id, api_key
    #     )

    return create_matrices(
        places, api_key_id, api_key,
        is_mock_enabled=False, mock_api_response=None
    )