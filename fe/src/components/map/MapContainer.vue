<template>
  <div id="map" class="map-view"></div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useNaverMap } from '@/services/useNaverMap'
import { useMapStore } from '@/store/map'
import type { PlaceMarker } from '@/types/domain/place'

const props = defineProps<{
  places: PlaceMarker[]
}>()

const mapStore = useMapStore()

const centerLat = props.places[0]?.coord.lat ?? 33.4
const centerLng = props.places[0]?.coord.lng ?? 126.55

// 지도 초기화
const { map } = useNaverMap(centerLat, centerLng)

// map 초기화 후 핀 세팅
watch(map, (newMap) => {
  if (newMap) {
    mapStore.setMap(newMap)
    mapStore.clearMarkers()
    console.log('✅ 지도 준비 완료:', newMap)
  }
})
</script>

<style scoped>
.map-view {
  width: 100%;
  height: 100%;
}
</style>
