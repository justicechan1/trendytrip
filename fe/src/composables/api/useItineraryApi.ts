// src/composables/api/useItineraryApi.ts

import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type { RawInitResponse } from '@/types/api/raw'
import type { ItineraryRequest, ItineraryResponse } from '@/types/api/trip'

export function useItineraryApi() {
  const { postData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function createItineraryRaw(
    body: any
  ): Promise<ApiResult<RawInitResponse>> {
    isLoading.value = true;
    error.value = null;

    try {
      const resp = await postData<RawInitResponse>(
        '/api/users/schedules/init',
        body
      );

      if (!resp.success || !resp.data) {
        throw new Error('일정 응답이 비어 있습니다');
      }

      // 백엔드 응답의 success 필드도 체크
      if (!resp.data.success) {
        throw new Error(resp.data.error || '일정 생성에 실패했습니다');
      }

      return { success: true, data: resp.data, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[useItineraryApi] error:', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchItinerary(
    request: ItineraryRequest
  ): Promise<ApiResult<ItineraryResponse>> {
    isLoading.value = true;
    error.value = null;

    try {
      const resp = await postData<ItineraryResponse>(
        '/api/users/schedules/itinerary',
        request
      );

      if (!resp.success || !resp.data) {
        throw new Error('여정 상세 정보 응답이 비어 있습니다');
      }

      return { success: true, data: resp.data, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[useItineraryApi] fetchItinerary error:', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return {
    createItineraryRaw,
    fetchItinerary,
    isLoading,
    error,
  };
}
