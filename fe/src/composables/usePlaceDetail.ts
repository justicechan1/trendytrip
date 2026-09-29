// src/composables/usePlaceDetail.ts

import { ref } from 'vue';
import { usePlaceDetailApi } from '@/composables/api/usePlaceDetailApi';

import type { ApiResult } from '@/types/api';
import type { PlaceDetailRequest } from '@/types/api/place.dto';
import type { RawPlaceDetailRequest, RawPlaceDetailResponse } from '@/types/api/raw'
import type { PlaceDetail } from '@/types/domain/place';

export function usePlaceDetail() {
  const placeDetail = ref<PlaceDetail | null>(null);
  const { fetchRawPlace, isLoading, error } = usePlaceDetailApi();

  const fetchPlaceDetail = async (payload: PlaceDetailRequest) => {
    // 1) 요청 변환
    const rawReq: RawPlaceDetailRequest = { name: payload.name };

    // 2) RAW API 호출
    const { success, data, error: err }:
      ApiResult<RawPlaceDetailResponse['places']> = await fetchRawPlace(rawReq);

    if (success && data) {
      // 3) RAW → 도메인 매핑
      placeDetail.value = {
        name: data.name,
        category: data.category,
        description: data.description,
        coord: { lng: data.x_cord, lat: data.y_cord },
        address: data.address,
        openTime: data.open_time,
        closeTime: data.close_time,
        conveniences: [data.convenience],
        images: data.image_urls,
      };
    } else {
      placeDetail.value = null;
      console.warn('[usePlaceDetail] 상세정보 불러오기 실패:', err);
    }
  };

  return { placeDetail, fetchPlaceDetail, isLoading, error };
}
