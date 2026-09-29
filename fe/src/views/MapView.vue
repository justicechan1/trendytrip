<template>
  <div class="map-page">
    <div class="map-wrapper">
      <MapContainer class="map-bg" :places="markerPlaces" />

      <Sidebar />

      <CategoryButton :categoryList="CATEGORY_LIST" :selectedCategory="selectedCategory"
        @select-category="handleCategoryClick" />

      <div class="hashtag-container ">
      <div id="hashtag_btn" v-if="showHashtag">
        <HashtagButton :selectedHashtag="selectedHashtag" :hashtags="hashtags" @select-hashtag="handleSelectHashtag" />
      </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useItineraryStore } from '@/store/itinerary'
import { useMapStore } from '@/store/map'

import MapContainer from '@/components/map/MapContainer.vue'
import Sidebar from '@/components/map/Sidebar.vue'
import HashtagButton from '@/components/ui/buttons/HashtagButton.vue'
import CategoryButton from '@/components/ui/buttons/CategoryButton.vue'

import { useCategoryHashtags } from '@/composables/useCategoryHashtags'
import { useHashtagToPlace } from '@/composables/useHashtagToPlace'
import { CATEGORY_LIST } from '@utils/constants'

import type { Hashtag, Category } from '@/types/common'

import '@/styles/map.css'

const itineraryStore = useItineraryStore()
const mapStore = useMapStore()

const markerPlaces = computed(() => {
  const current = itineraryStore.current
  const selectedDay = itineraryStore.state.selectedDay || 0
  if (!current) return []
  const firstPlace = current.placesByDay[selectedDay]?.[0]
  if (!firstPlace) {
    console.warn(`⚠️ Day ${selectedDay+1}에 장소가 없습니다.`)
    return []
  }

  return [{
    name: firstPlace.name,
    category: firstPlace.category,
    coord: {
      lng: firstPlace.coord.lng,
      lat: firstPlace.coord.lat
    }
  }]
})

// 카테고리 해시태그 관련 훅
const {
  showHashtag,
  selectedCategory,
  hashtags,
  toggleCategory,
} = useCategoryHashtags()

// 해시태그 관련 훅
const {
  selectedHashtag,
  selectHashtag,
} = useHashtagToPlace()

// 카테고리 클릭
const handleCategoryClick = async (category: Category) => {
  const bounds = mapStore.getBounds()
  if (!bounds) {
    alert('지도를 불러올 수 없습니다. 다시 시도해주세요.')
    return
  }

  console.log(`🔍 카테고리 클릭: ${category}`, bounds)
  await toggleCategory(category, bounds)
  mapStore.clearMarkers()
  mapStore.clearPolylines()
}

// 해시태그 클릭
const handleSelectHashtag = async (hashtag: Hashtag) => {
  const bounds = mapStore.getBounds()
  if (!bounds) {
    alert('지도를 불러올 수 없습니다. 다시 시도해주세요.')
    return
  }

  const category = selectedCategory.value
  if (!category) {
    alert('카테고리를 먼저 선택해주세요.')
    return
  }
  mapStore.clearMarkers()
  mapStore.clearPolylines()
  console.log(`🔍 해시태그 클릭: ${hashtag.name}, 지도 범위:`, bounds)
  await selectHashtag(category, hashtag, bounds)
}
</script>

<style scoped>
.hashtag-container {
  position: absolute;
  top: 10vw;
  right: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  width: 300px;
  height: 300px;
  background-color: none;
  border-radius: 5px;
  overflow-y: auto;
  scrollbar-width: none;
  z-index: 300;
}

</style>