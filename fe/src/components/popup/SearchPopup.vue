<template>
  <div class="popup-container">
    <header>
      <p>어떤 관광명소를 찾고 계시나요?</p>
      <h3>🔎 장소를 검색해주세요</h3>
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="장소를 입력하세요"
          class="input-search"
          aria-label="장소 검색"
          @input="onSearchInput"
          @keyup.enter="searchPlaces"
        />
        <button @click="searchPlaces" class="search-button">검색</button>
      </div>
      <p v-if="isLoading">로딩 중...</p>
      <p v-if="error" class="error-text">검색 중 오류가 발생했습니다.</p>
    </header>

    <PlaceList
      :places="places"
      :keyword="searchQuery"
      @select="selectPlace"
    />

    <footer>
      <button class="button-close" @click="emit('close')">닫기 ❌</button>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import PlaceList from '@/components/common/PlaceList.vue';
import { usePlaceSearch } from '@/composables/usePlaceSearch';
import type { PlaceSearchHit } from '@/types/api/place.dto'; 

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'get-place-info', place: PlaceSearchHit): void;
}>();

const searchQuery = ref('');
const {
  searchPlaces: fetchPlaceNames,
  results,
  isLoading,
  error,
} = usePlaceSearch();

const places = computed(() => results.value);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    performSearch();
  }, 300);
}

async function performSearch() {
  console.debug('검색 요청:', searchQuery.value);
  await fetchPlaceNames({ keyword: searchQuery.value });
}

async function searchPlaces() {
  if (debounceTimer) clearTimeout(debounceTimer);
  await performSearch();
}

function selectPlace(place: PlaceSearchHit) {
  console.debug('선택된 장소:', place);
  emit('get-place-info', place); 
}
</script>

<style scoped>
@import "@/styles/popup.css";

.search-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-search {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.search-button {
  padding: 8px 16px;
  background-color: skyblue;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.search-button:hover {
  background-color: deepskyblue;
}

.place-list ul {
  list-style-type: none;
  padding: 0;
  overflow-y: auto;
  max-height: 200px;
}

.place-list li {
  padding: 8px;
  cursor: pointer;
  border-bottom: 1px solid #ccc;
}

.place-list li:hover {
  background-color: #f0f0f0;
}
</style>