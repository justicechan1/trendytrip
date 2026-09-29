// src/composables/api/usePlaceDetailApi.ts

import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type { RawPlaceDetailRequest, RawPlaceDetailResponse } from '@/types/api/raw'

export function usePlaceDetailApi() {
  const { getData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetchRawPlace(
    body: RawPlaceDetailRequest
  ): Promise<ApiResult<RawPlaceDetailResponse['places']>> {
    isLoading.value = true;
    error.value = null;
    console.debug('[usePlaceDetailApi] 요청(raw):', body);

    try {
      const resp = await getData<RawPlaceDetailResponse>(
        '/api/places/select_place',
        body
      );
      console.debug('[usePlaceDetailApi] 응답(raw):', resp);

      if (!resp.success || !resp.data || typeof resp.data.places !== 'object') {
        throw new Error('장소 상세(raw) 응답이 없습니다');
      }

      return { success: true, data: resp.data.places, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[usePlaceDetailApi] 실패(raw):', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return { fetchRawPlace, isLoading, error };
}

