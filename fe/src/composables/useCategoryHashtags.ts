import { ref } from 'vue';
import { useCategoryToHashtagApi } from '@/composables/api/useCategoryToHashtagApi';
import type { Hashtag, Viewport, Category } from '@/types/common';
import type { ApiResult } from '@/types/api';

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

export function useCategoryHashtags() {
  const showHashtag = ref(false);
  const selectedCategory = ref<Category | null>(null);
  const hashtags = ref<Hashtag[]>([]);

  const { fetchRawTags } = useCategoryToHashtagApi();

  const toggleCategory = async (category: Category, bounds: any) => {
    if (selectedCategory.value === category && showHashtag.value) {
      showHashtag.value = false;
      return;
    }

    selectedCategory.value = category;

    console.info('[useCategoryHashtags] 선택된 카테고리:', category);
    console.info('[useCategoryHashtags] 지도 bounds:', bounds);

    const viewport: Viewport = transformBoundsToViewport(bounds);
    const rawViewport = transformViewportToApi(viewport);

    const rawReq = {
      category,
      viewport: rawViewport,
    };

    console.info('[useCategoryHashtags] 전송할 요청:', rawReq);

    const { success, data, error }: ApiResult<{ hashtag: string }[]> =
      await fetchRawTags(rawReq);

    if (success && data) {
      hashtags.value = data.map((item) => ({
        name: item.hashtag,
      }));
      showHashtag.value = true;
    } else {
      hashtags.value = [];
      showHashtag.value = false;
      console.warn('[useCategoryHashtags] 해시태그 로딩 실패:', error);
    }
  };

  return {
    showHashtag,
    selectedCategory,
    hashtags,
    toggleCategory,
  };
}
