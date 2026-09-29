<template>
  <div class="style-section">
    <!-- 여행 스타일 선택 -->
    <div class="style-title center-text">
      <p class="style-subtitle">어떤 여행 스타일을 원하세요?</p>
      <h3 class="style-heading">원하는 여행 스타일을 선택해주세요🎆</h3>
    </div>

    <div class="style-grid">
      <!-- 여행 스타일 -->
      <div class="style-grid2">
        <h4> Q1. 어떤 여행을 원하세요? </h4>
        <button
          class="style-button"
          :class="{ selected: selectedStyle==='relaxed' }"
          @click="selectStyle('relaxed')"
        >여유로운</button>
        <button
          class="style-button"
          :class="{ selected: selectedStyle==='active' }"
          @click="selectStyle('active')"
        >활동적인</button>
      </div>

      <!-- 지역 선택 (지도) -->
      <div class="region-select-section">
        <h4> Q2. 어떤 지역을 여행하고 싶으신가요?</h4>
        <p class="region-hint">지도에서 원하는 지역을 클릭하세요 (복수 선택 가능)</p>
        <JejuMap
          v-model="selectedAreas"
          @region-change="handleRegionChange"
        />
      </div>

      <!-- 해시태그 -->
      <div class="style-grid2">
        <h4> Q3. 선택한 지역에서 어떤 감성을 찾고 있나요?</h4>

        <!-- 검색창 -->
        <div class="search-container">
          <input type="text" placeholder="해시태그 검색" class="input-search" v-model="searchQuery"/>
        </div>

        <div class="hashtag-list scroll-box">
          <button
            v-for="tag in filteredHashtags"
            :key="tag.name"
            class="style-button"
            :class="{ selected: selectedHashtags.some(t => t.name === tag.name) }"
            @click="toggleHashtag(tag)"
          >
            {{ tag.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 하단 버튼 -->
    <footer class="style-footer flex-between">
      <button class="button-base button-prev" @click="emit('prev')">이전</button>
      <button class="button-base button-next" @click="saveSelections">다음</button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/store/user'
import type { Hashtag } from '@/types/common'
import { fetchHashtags } from '@composables/api/useHashtagSearchApi'
import JejuMap from '@/components/common/JejuMap.vue'

const emit = defineEmits<{
  (e:'prev'): void
  (e:'next'): void
}>()

const userStore = useUserStore()

// 여행 스타일
const selectedStyle = ref('')
function selectStyle(style: string) {
  selectedStyle.value = style
}

// 지역 선택 및 해시태그 관리
const selectedAreas = ref<string[]>([])
const areaHashtags = ref<Map<string, Hashtag[]>>(new Map())
const selectedHashtags = ref<Hashtag[]>([])

// 검색용
const searchQuery = ref('')

// 모든 선택된 지역 해시태그를 병합
const mergedHashtags = computed(() => {
  const all: Hashtag[] = []
  areaHashtags.value.forEach(tags => all.push(...tags))
  return all
})

// 검색 적용 (지역 병합 시 수천 개까지 나와 렌더링이 느려지므로 상한 적용)
const HASHTAG_LIMIT = 100
const filteredHashtags = computed(() => {
  const base = searchQuery.value
    ? mergedHashtags.value.filter(tag => tag.name.includes(searchQuery.value))
    : mergedHashtags.value
  return base.slice(0, HASHTAG_LIMIT)
})

// 지역 선택 변경 핸들러 (지도 컴포넌트에서 호출)
async function handleRegionChange(area: string, selected: boolean) {
  if (!selected) {
    // 선택 취소 → 해당 지역 해시태그 제거
    areaHashtags.value.delete(area)
    selectedHashtags.value = selectedHashtags.value.filter(tag => !areaHashtags.value.get(area)?.some(t => t.name === tag.name))
  } else {
    // 선택 → 해당 지역 해시태그 불러오기
    try {
      const res = await fetchHashtags(area)
      areaHashtags.value.set(area, res)
    } catch (err) {
      console.error(err)
    }
  }
}

// 해시태그 선택/취소
function toggleHashtag(tag: Hashtag) {
  const exists = selectedHashtags.value.some(t => t.name === tag.name)
  if (exists) selectedHashtags.value = selectedHashtags.value.filter(t => t.name !== tag.name)
  else selectedHashtags.value.push(tag)
}

// 선택 완료 → 한 번에 저장
function saveSelections() {
  userStore.setStyle(selectedStyle.value)
  userStore.setJejuAreas(selectedAreas.value)
  userStore.setTags(selectedHashtags.value)

  emit('next')
}
</script>


<style scoped>
/* 전체 컨테이너 */
.style-section {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 30px;
  font-family: 'Noto Sans KR', sans-serif;
  background-color: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  max-height: 85vh;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* 제목 */
.style-title {
  margin-bottom: 25px;
  text-align: center;
}

.style-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 8px;
}

.style-heading {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

/* 버튼 그리드 */
.style-grid {
  display: grid;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.style-grid2 {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.style-grid2 h4 {
  flex-basis: 100%;
  margin-bottom: 8px;
}

/* 지역 선택 섹션 */
.region-select-section {
  margin-bottom: 12px;
}

.region-select-section h4 {
  margin-bottom: 8px;
}

.region-hint {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 12px;
}

/* 버튼 */
.style-button {
  padding: 10px 20px;
  background-color: #f0fbfc;
  border: 2px solid #b2ebf2;
  border-radius: 8px;
  font-size: 1rem;
  color:#00acc1;
  cursor: pointer;
  transition: all 0.25s ease;
}

.style-button:hover {
  background-color: #00bcd4;
  color: white;
}

.style-button.selected {
  background-color: #00bcd4;
  color: white;
  border-color: #00acc1;
  font-weight: bold;
}

/* 검색창 */
.search-container {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.input-search {
  flex: 1;
  padding: 10px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.25s ease;
}

.input-search:focus {
  border-color: #00acc1;
  outline: none;
}

.search-button {
  padding: 10px 18px;
  background-color: #00acc1;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.25s ease;
}

.search-button:hover {
  background-color: #2563eb;
}

/* 하단 버튼 */
.style-footer {
  margin-top: 30px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
}

.button-base {
  padding: 10px 20px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
}

scroll-box {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  max-height: 200px; /* 원하는 높이로 조정 가능 */
  overflow-y: auto; /* 세로 스크롤 */
  padding-right: 5px; /* 스크롤 공간 확보 */
}

/* 스크롤바 꾸미기(Optional) */
.scroll-box::-webkit-scrollbar {
  width: 6px;
}

.scroll-box::-webkit-scrollbar-thumb {
  background-color: rgba(0, 172, 193, 0.5);
  border-radius: 3px;
}

.scroll-box::-webkit-scrollbar-track {
  background-color: transparent;
}

.scroll-box {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  max-height: 150px;
  overflow-y: auto;
  padding-right: 5px;
  align-content: flex-start;
}
</style>
