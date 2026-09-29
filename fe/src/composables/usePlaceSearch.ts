// src/composables/usePlaceSearch.ts

import { ref } from 'vue';
import { usePlaceSearchApi } from '@/composables/api/usePlaceSearchApi';
import type {
  PlaceSearchRequest,
  PlaceSearchHit,
} from '@/types/api/place.dto';
import type { RawPlaceSearchResponse, RawPlaceSearchRequest } from '@/types/api/raw'
import type { ApiResult } from '@/types/api';

export function usePlaceSearch() {
  const keyword = ref<PlaceSearchRequest['keyword']>('');
  const results = ref<PlaceSearchHit[]>([]);
  const { fetchRawSearch, isLoading, error } = usePlaceSearchApi();

  async function searchPlaces(request: PlaceSearchRequest) {
    // 1) 내부 요청 → raw 요청 변환
    const rawReq: RawPlaceSearchRequest = { name: request.keyword };

    // 2) raw API 호출
    const { success, data, error: err }:
      ApiResult<RawPlaceSearchResponse['search']> = await fetchRawSearch(rawReq);

    if (success && data) {
      // 3) raw 응답 → 내부 모델 매핑
      results.value = data.map((item) => ({
        name: item.name,
      }));
    } else {
      results.value = [];
      console.error('[usePlaceSearch] 검색 실패:', err);
    }
  }

  return {
    keyword,
    results,
    isLoading,
    error,
    searchPlaces,
  };
}
