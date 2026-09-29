// src/composables/useItinerary.ts

import type {
  ItineraryPostBody,
  ItineraryResponse,
} from '@/types/api/itinerary.dto';
import type { ApiResult } from '@/types/api';
import type { InternalItinerary, ItineraryPlace } from '@/types/domain/itinerary';

import { useItineraryApi } from '@/composables/api/useItineraryApi';
import { convertPlaceSummaryToItineraryPlace } from '@/utils/converters';
import {
  wrapItineraryPayload,
  wrapInitResponse,
} from '@/utils/apiWrapper';

export function useItinerary() {
  const { createItineraryRaw, isLoading, error } = useItineraryApi();

  async function createItinerary(
    body: ItineraryPostBody
  ): Promise<ApiResult<InternalItinerary>> {

    // 내부에서 0-base로 변환된 데이터
    const wrappedBody = wrapItineraryPayload(body);

    // API 호출 전 1-base로 변환
    const result = await createItineraryRaw(wrappedBody);

    if (!result.success || !result.data) {
      return { success: false, data: null, error: result.error };
    }

    // Init API 응답을 프론트엔드 형식으로 변환
    const wrappedResponse: ItineraryResponse = wrapInitResponse(result.data);

    console.log('[useItinerary] wrappedResponse:', wrappedResponse);

    const rawPlaces = wrappedResponse.placesByDay;
    const rawPaths = wrappedResponse.pathsByDay;
    const converted: Record<number, ItineraryPlace[]> = {};

    console.log('[useItinerary] rawPlaces:', rawPlaces);
    console.log('[useItinerary] rawPaths:', rawPaths);

    // 0-base로 데이터를 내부적으로 처리
    for (const [dayKey, list] of Object.entries(rawPlaces)) {
      const day = Number(dayKey);

      // dayKey가 정상적인 숫자인지 체크
      if (isNaN(day)) {
        console.warn(`[useItinerary] 잘못된 dayKey 발견: ${dayKey}`);
        continue; // 잘못된 dayKey는 처리하지 않음
      }

      const arr: ItineraryPlace[] = [];

      for (const summary of list) {
        try {
          arr.push(convertPlaceSummaryToItineraryPlace(summary));
        } catch (convErr) {
          console.warn(`[useItinerary] 변환 실패 (day=${day}):`, summary, convErr);
        }
      }

      // day를 0-base로 변환
      converted[day] = arr;
    }

    const internal: InternalItinerary = {
      placesByDay: converted,
      pathsByDay: rawPaths  // pathsByDay 추가!
    };

    console.log('[useItinerary] internal:', internal);
    return { success: true, data: internal, error: null };
  }

  return {
    createItinerary,
    isLoading,
    error,
  };
}
