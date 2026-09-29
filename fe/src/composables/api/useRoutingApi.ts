// src/composables/api/useRoutingApi.ts

import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type {
  RawRoutingRequestDto,
  RawRoutingResponseDto,
} from '@/types/api/raw';

export function useRoutingApi() {
  const { postData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetchRawRoute(
    body: RawRoutingRequestDto
  ): Promise<ApiResult<RawRoutingResponseDto>> {
    isLoading.value = true;
    error.value = null;

    try {
      const resp = await postData<RawRoutingResponseDto>(
        '/api/trip-planner/schedule',
        body
      );
      if (!resp.success || !resp.data) {
        throw new Error('경로 계산 응답이 없습니다.');
      }
      return { success: true, data: resp.data, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[useRoutingApi] 오류:', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return { fetchRawRoute, isLoading, error };
}
