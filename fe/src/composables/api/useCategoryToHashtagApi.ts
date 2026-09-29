// src/composables/api/useCategoryToHashtagApi.ts

import { ref } from 'vue';
import { useTrendyTripApi } from '@/composables/useTrendyTripApi';
import type { ApiResult } from '@/types/api';
import type { RawCategoryToHashtagRequest, RawCategoryToHashtagResponse } from '@/types/api/raw'

export function useCategoryToHashtagApi() {
  const { postData } = useTrendyTripApi();
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetchRawTags(
    body: RawCategoryToHashtagRequest
  ): Promise<ApiResult<RawCategoryToHashtagResponse['tag']>> {
    isLoading.value = true;
    error.value = null;

    console.info('[useCategoryToHashtagApi] 요청(raw):', body);
    try {
      const resp = await postData<RawCategoryToHashtagResponse>(
        '/api/users/maps/hashtage',
        body
      );

      console.info('[useCategoryToHashtagApi] 응답(raw):', resp);
      if (!resp.success || !resp.data || !Array.isArray(resp.data.tag)) {
        throw new Error('해시태그 응답이 없습니다');
      }
      return { success: true, data: resp.data.tag, error: null };
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      console.error('[useCategoryToHashtagApi] 실패(raw):', err);
      return { success: false, data: null, error: err };
    } finally {
      isLoading.value = false;
    }
  }

  return { fetchRawTags, isLoading, error };
}
