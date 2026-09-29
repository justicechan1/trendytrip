// src/composables/useHashtagToPlace.ts
import { ref } from 'vue';
import { useHashtagToPlaceApi } from '@/composables/api/useHashtagToPlaceApi';
import type { Hashtag, Viewport, Category } from '@/types/common';
import type { HashtagToPlaceResponse } from '@/types/api/hashtag.dto';
import type { RawHashtagToPlaceRequest } from '@/types/api/raw';
import type { ApiResult } from '@/types/api';
import { useMapStore } from '@/store/map'
import type { PlaceSummary } from '@/types/api/itinerary.dto'

// bounds → Viewport 변환
function transformBoundsToViewport(bounds: any): Viewport {
  return {
    minX: bounds._sw?.x ?? bounds._min?.x ?? 0,
    minY: bounds._sw?.y ?? bounds._min?.y ?? 0,
    maxX: bounds._ne?.x ?? bounds._max?.x ?? 0,
    maxY: bounds._ne?.y ?? bounds._max?.y ?? 0,
  };
}

// Viewport → API용 snake_case 변환
function transformViewportToApi(viewport: Viewport) {
  return {
    min_x: viewport.minX,
    min_y: viewport.minY,
    max_x: viewport.maxX,
    max_y: viewport.maxY,
  };
}

export function useHashtagToPlace() {
  const selectedHashtag = ref<Hashtag | null>(null);
  const { fetchRawRecommendations, isLoading, error } = useHashtagToPlaceApi();

  const selectHashtag = async (
    category: Category,
    hashtag: Hashtag,
    bounds: any
  ): Promise<ApiResult<HashtagToPlaceResponse>> => {
    selectedHashtag.value = hashtag;
    console.info('[useHashtagToPlace] 선택된 해시태그:', hashtag);
    console.info('[useHashtagToPlace] 지도 bounds:', bounds);

    // 1) bounds → viewport
    const viewport = transformBoundsToViewport(bounds);
    const rawViewport = transformViewportToApi(viewport);

    // 2) internal → raw request
    const rawReq: RawHashtagToPlaceRequest = {
      category,
      tag: [{ hashtag }],
      viewport: rawViewport,
    };

    console.info('[useHashtagToPlace] 전송할 요청:', rawReq);
    const { success, data, error: err } = await fetchRawRecommendations(rawReq);

    if (!success || !data) {
      console.warn('[useHashtagToPlace] 장소 추천 실패(raw):', err);
      return { success: false, data: null, error: err };
    }

    // 3) raw → internal model mapping
    const recommendations = data.map((item) => ({
      name: item.name,
      category: item.category,
      coord: { lng: item.x_cord, lat: item.y_cord },
      similarity: item.similarity,
    }));

    const mapStore = useMapStore()

    recommendations.forEach((place) => {
      const placeSummary: PlaceSummary = {
        ...place,
      };

      mapStore.addPlaceMarker(placeSummary);
    });

    console.info('[useHashtagToPlace] 매핑된 추천 장소:', recommendations);

    const internalRes: HashtagToPlaceResponse = { recommendations };
    return { success: true, data: internalRes, error: null };
  };

  return { selectedHashtag, isLoading, error, selectHashtag };
}