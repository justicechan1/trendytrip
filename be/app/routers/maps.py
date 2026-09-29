from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Tuple, List
import numpy as np

from app.database import get_db

from app.models.hashtag import Hashtag
from app.models.hashtag_mapping import (
    CafeHashtagMap, HotelHashtagMap, RestaurantHashtagMap, TourHashtagMap
)
from app.models.jeju_cafe import JejuCafe
from app.models.jeju_hotel import JejuHotel
from app.models.jeju_restaurant import JejuRestaurant
from app.models.jeju_tour import JejuTour

from app.schemas.maps import (
    HashtageIn, HashtageOut, HashtagOnly,
    SelectHashtageIn, SelectHashtageOut, SelectHashtageOutItem,
    LocalHashtagIn, LocalHashtagOut
)
from app.core.errors import BadRequestError, NotFoundError 
from ._utils import _json_vec, _viewport_filter
from app.core.vector import normalize_vectors
router = APIRouter(prefix="/api/users/maps", tags=["maps"])

# 카테고리 표기 정규화(한글/영문/대소문자)
CATEGORY_ALIAS: Dict[str, str] = {
    "cafe": "cafe", "카페": "cafe", "Cafe": "cafe", "CAFE": "cafe",
    "hotel": "hotel", "숙소": "hotel", "Hotel": "hotel", "HOTEL": "hotel",
    "accommodation": "hotel",  # 프론트엔드에서 사용하는 숙소 카테고리
    "restaurant": "restaurant", "음식점": "restaurant",
    "Restaurant": "restaurant", "RESTAURANT": "restaurant",
    "tour": "tour", "관광지": "tour", "Tour": "tour", "TOUR": "tour",
    "tourist": "tour",  # 프론트엔드에서 사용하는 관광지 카테고리
    "transport": "transport", "교통": "transport",  # 교통 카테고리
}
def _norm_cat(c: str) -> str:
    return CATEGORY_ALIAS.get(c, c).lower()

# (PlaceModel, MapModel, fk_on_map, pk_on_place, x_col, y_col)
JOIN_INFO: Dict[str, Tuple] = {
    "cafe":       (JejuCafe,       CafeHashtagMap,       CafeHashtagMap.cafe_id,       JejuCafe.cafe_id,       JejuCafe.x_cord,       JejuCafe.y_cord),
    "hotel":      (JejuHotel,      HotelHashtagMap,      HotelHashtagMap.hotel_id,     JejuHotel.hotel_id,     JejuHotel.x_cord,      JejuHotel.y_cord),
    "restaurant": (JejuRestaurant, RestaurantHashtagMap, RestaurantHashtagMap.restaurant_id, JejuRestaurant.restaurant_id, JejuRestaurant.x_cord, JejuRestaurant.y_cord),
    "tour":       (JejuTour,       TourHashtagMap,       TourHashtagMap.tour_id,       JejuTour.tour_id,       JejuTour.x_cord,       JejuTour.y_cord),
}

@router.post("/hashtage", response_model=HashtageOut)
def hashtage(req: HashtageIn, db: Session = Depends(get_db)):
    cat = _norm_cat(req.category)
    if cat not in JOIN_INFO:
        return HashtageOut(tag=[])

    Place, Map, fk_on_map, pk_on_place, x_c, y_c = JOIN_INFO[cat]

    rows = (
        db.query(Hashtag.hashtag, func.count().label("cnt"))
        .join(Map, Map.hashtag_id == Hashtag.hashtag_id)
        .join(Place, fk_on_map == pk_on_place)               
        .filter(_viewport_filter(x_c, y_c, req.viewport))
        .group_by(Hashtag.hashtag)
        .order_by(func.count().desc())
        .all()
    )
    return HashtageOut(tag=[HashtagOnly(hashtag=h) for (h, _) in rows])

@router.post("/select_hashtage", response_model=SelectHashtageOut)
def select_hashtage(req: SelectHashtageIn, db: Session = Depends(get_db)):
    # 카테고리 정규화 적용
    cat = _norm_cat(req.category)
    # 카테고리 테이블/매핑 정보 선택
    Place, Map, fk_on_map, pk_on_place, x_c, y_c = JOIN_INFO.get(cat, (None,)*6)
    if Place is None or not req.tag:
        return SelectHashtageOut(select_hashtage=[])

    # 1) 입력 해시태그 임베딩(q)
    tag_str = req.tag[0].hashtag
    row = db.query(Hashtag.embeddings).filter(Hashtag.hashtag == tag_str).first()
    if not row:
        return SelectHashtageOut(select_hashtage=[])
    q = _json_vec(row.embeddings)
    if q is None:
        return SelectHashtageOut(select_hashtage=[])
    q = q / (np.linalg.norm(q) + 1e-8)

    # 2) 단일 조인으로 뷰포트 내 (place, hashtag) 전부 가져오기
    rows = (
        db.query(
            fk_on_map.label("pid"),
            Place.name.label("name"),
            Place.x_cord.label("x"),
            Place.y_cord.label("y"),
            Hashtag.embeddings.label("emb")
        )
        .select_from(Map)
        .join(Place, fk_on_map == pk_on_place)
        .join(Hashtag, Hashtag.hashtag_id == Map.hashtag_id)
        .filter(_viewport_filter(Place.x_cord, Place.y_cord, req.viewport))
        .all()
    )
    if not rows:
        return SelectHashtageOut(select_hashtage=[])

    # 3) 벡터화 준비 (한 번에 정규화/내적)
    pids, names, xs, ys, vecs = [], [], [], [], []
    for r in rows:
        v = _json_vec(r.emb)
        if v is not None:
            pids.append(int(r.pid))
            names.append(r.name)
            xs.append(float(r.x))
            ys.append(float(r.y))
            vecs.append(v)
    if not vecs:
        return SelectHashtageOut(select_hashtage=[])

    E = np.vstack(vecs).astype(np.float32)      # (M, D)
    E = normalize_vectors(E, axis=1)            # 행 정규화 1회
    sims = E.dot(q).astype(np.float32)          # (M,)

    # 4) place_id(pid) 별 최대 유사도 집계 (넘파이로 그룹 max)
    pids = np.asarray(pids, dtype=np.int64)
    order = np.argsort(pids)
    p_sorted = pids[order]
    s_sorted = sims[order]

    uniq_pid, idx_start = np.unique(p_sorted, return_index=True)
    max_sims = np.maximum.reduceat(s_sorted, idx_start)  # 각 pid 구간의 최대값

    # 5) Top-5 선택
    k = min(5, max_sims.size)
    if k == 0:
        return SelectHashtageOut(select_hashtage=[])
    top_idx = np.argpartition(-max_sims, k-1)[:k]
    top_idx = top_idx[np.argsort(-max_sims[top_idx])]
    top_pids = uniq_pid[top_idx]
    top_scores = max_sims[top_idx]

    # 6) pid → 대표 name/x/y (첫 등장 인덱스 사용)
    #    같은 pid 행들은 동일한 place를 가리키므로 첫 번째 것을 사용
    first_index_by_pid = {}
    for i, pid in enumerate(p_sorted):
        if pid not in first_index_by_pid:
            first_index_by_pid[pid] = i

    names = np.asarray(names, dtype=object)[order]
    xs = np.asarray(xs, dtype=np.float32)[order]
    ys = np.asarray(ys, dtype=np.float32)[order]

    out = []
    for pid, score in zip(top_pids, top_scores):
        i = first_index_by_pid[pid]
        out.append(
            SelectHashtageOutItem(
                name=str(names[i]),
                category=req.category,
                x_cord=float(xs[i]),
                y_cord=float(ys[i]),
                similarity=float(score)
            )
        )
    return SelectHashtageOut(select_hashtage=out)

REGION_CODE_MAP: Dict[str, int] = {
    "제주시": 10,
    "애월읍": 101,
    "한림읍": 102,
    "한경면": 103,
    "조천읍": 104,
    "구좌읍": 105,
    "서귀포시": 20,
    "성산읍": 201,
    "표선면": 202,
    "남원읍": 203,
    "안덕면": 204,
    "대정읍": 205,
    "중문": 206,
}

@router.post("/local_hashtag", response_model=LocalHashtagOut, summary="지역에 따른 해시태그 출력")
def local_hashtag(body: LocalHashtagIn, db: Session = Depends(get_db)):
    local_name = body.local_name.strip()
    if local_name not in REGION_CODE_MAP:
        raise BadRequestError(message=f"알 수 없는 지역명: {local_name}")

    code = REGION_CODE_MAP[local_name]

    q_cafe = (
        db.query(Hashtag.hashtag.label("tag"))
        .join(CafeHashtagMap, CafeHashtagMap.hashtag_id == Hashtag.hashtag_id)
        .join(JejuCafe, JejuCafe.cafe_id == CafeHashtagMap.cafe_id)
        .filter(JejuCafe.location_code == code)
    )
    q_rest = (
        db.query(Hashtag.hashtag.label("tag"))
        .join(RestaurantHashtagMap, RestaurantHashtagMap.hashtag_id == Hashtag.hashtag_id)
        .join(JejuRestaurant, JejuRestaurant.restaurant_id == RestaurantHashtagMap.restaurant_id)
        .filter(JejuRestaurant.location_code == code)
    )
    q_hotel = (
        db.query(Hashtag.hashtag.label("tag"))
        .join(HotelHashtagMap, HotelHashtagMap.hashtag_id == Hashtag.hashtag_id)
        .join(JejuHotel, JejuHotel.hotel_id == HotelHashtagMap.hotel_id)
        .filter(JejuHotel.location_code == code)
    )
    q_tour = (
        db.query(Hashtag.hashtag.label("tag"))
        .join(TourHashtagMap, TourHashtagMap.hashtag_id == Hashtag.hashtag_id)
        .join(JejuTour, JejuTour.tour_id == TourHashtagMap.tour_id)
        .filter(JejuTour.location_code == code)
    )

    rows = q_cafe.union(q_rest, q_hotel, q_tour).all()
    if not rows:
        raise NotFoundError(message=f"해당 지역({local_name})에 대한 해시태그가 없습니다.")

    return LocalHashtagOut(tag=[HashtagOnly(hashtag=r.tag) for r in rows])