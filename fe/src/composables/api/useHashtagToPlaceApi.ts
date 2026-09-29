// src/composables/api/useHashtagToPlaceApi.ts
import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type { RawHashtagToPlaceRequest, RawHashtagToPlaceResponse } from '@/types/api/raw';

export function useHashtagToPlaceApi() {
  const { postData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetchRawRecommendations(
    body: RawHashtagToPlaceRequest
  ): Promise<ApiResult<RawHashtagToPlaceResponse['select_hashtage']>> {
    isLoading.value = true;
    error.value = null;

    console.debug('[useHashtagToPlaceApi] 요청(raw):', body);
    try {
      const resp = await postData<RawHashtagToPlaceResponse>(
        '/api/users/maps/select_hashtage',
        body
      );
      console.info('[useHashtagToPlaceApi] 응답(raw):', resp);

      if (!resp.success || !resp.data) {
        throw new Error('추천 장소 응답(raw)이 없습니다');
      }

      return { success: true, data: resp.data.select_hashtage, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[useHashtagToPlaceApi] 실패(raw):', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return { fetchRawRecommendations, isLoading, error };
}