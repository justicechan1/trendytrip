// src/composables/api/usePlaceSearchApi.ts

import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type {
  RawPlaceSearchRequest,
  RawPlaceSearchResponse,
} from '@/types/api/raw';

export function usePlaceSearchApi() {
  const { getData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetchRawSearch(
    body: RawPlaceSearchRequest
  ): Promise<ApiResult<RawPlaceSearchResponse['search']>> {
    isLoading.value = true;
    error.value = null;
    console.debug('[usePlaceSearchApi] 요청(raw):', body);

    try {

      const resp = await getData<RawPlaceSearchResponse>(
        '/api/places/search',
        {name:body.name}
      );
      console.debug('[usePlaceSearchApi] 응답(raw):', resp);

      if (!resp.success || !resp.data || !Array.isArray(resp.data.search)) {
        throw new Error('장소 검색(raw) 응답이 없습니다');
      }

      return { success: true, data: resp.data.search, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[usePlaceSearchApi] 실패(raw):', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return { fetchRawSearch, isLoading, error };
}