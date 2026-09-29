<template>
  <div class="jeju-map-wrapper">
    <div class="jeju-map-container">
      <svg
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        class="jeju-svg"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <!-- 그라데이션 -->
          <linearGradient id="oceanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#e1f5fe" />
            <stop offset="100%" stop-color="#b3e5fc" />
          </linearGradient>
          <linearGradient id="regionGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#c8e6c9" />
            <stop offset="100%" stop-color="#a5d6a7" />
          </linearGradient>
          <linearGradient id="selectedGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#4dd0e1" />
            <stop offset="100%" stop-color="#00acc1" />
          </linearGradient>
          <linearGradient id="hoverGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#80deea" />
            <stop offset="100%" stop-color="#4dd0e1" />
          </linearGradient>

          <!-- 그림자 필터 -->
          <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="2" dy="3" stdDeviation="3" flood-color="#000" flood-opacity="0.15"/>
          </filter>
        </defs>

        <!-- 바다 배경 -->
        <rect x="0" y="0" :width="svgWidth" :height="svgHeight" fill="url(#oceanGrad)" />

        <!-- 각 지역 폴리곤 -->
        <g class="regions">
          <path
            v-for="region in geoData"
            :key="region.properties.name"
            :d="getPath(region)"
            :class="[
              'region-path',
              {
                selected: isSelected(region.properties.name),
                hovered: hoveredRegion === region.properties.name
              }
            ]"
            @click="toggleRegion(region.properties.name)"
            @mouseenter="hoveredRegion = region.properties.name"
            @mouseleave="hoveredRegion = null"
          />
        </g>

        <!-- 지역 라벨 -->
        <g class="labels">
          <text
            v-for="region in geoData"
            :key="'label-' + region.properties.name"
            :x="getLabelPosition(region)[0]"
            :y="getLabelPosition(region)[1]"
            :class="['region-label', { 'label-selected': isSelected(region.properties.name) }]"
          >
            {{ region.properties.name }}
          </text>
        </g>

        <!-- 나침반 -->
        <g :transform="`translate(${svgWidth - 50}, 50)`">
          <circle cx="0" cy="0" r="25" fill="white" stroke="#90a4ae" stroke-width="2" opacity="0.95"/>
          <polygon points="0,-18 -5,6 0,2 5,6" fill="#e53935"/>
          <polygon points="0,18 -5,-6 0,-2 5,-6" fill="#78909c"/>
          <text x="0" y="-30" class="compass-text">N</text>
        </g>
      </svg>
    </div>

    <!-- 선택된 지역 카드 -->
    <div class="selected-card">
      <div class="card-header">
        <div class="card-title">
          <span class="card-icon">🗺️</span>
          <span>여행 지역</span>
        </div>
        <span class="card-badge">
          {{ selectedRegions.length > 0 ? `${selectedRegions.length}개 선택` : '미선택' }}
        </span>
      </div>

      <div class="card-content">
        <div class="selected-chips" v-if="selectedRegions.length > 0">
          <button
            v-for="region in selectedRegions"
            :key="region"
            class="chip"
            @click="toggleRegion(region)"
          >
            <span class="chip-text">{{ region }}</span>
            <span class="chip-remove">×</span>
          </button>
        </div>

        <div class="empty-state" v-else>
          <p>지도에서 방문하고 싶은 지역을 클릭해주세요</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import jejuGeoJson from '@/assets/jeju-map.json'

interface GeoFeature {
  type: string
  properties: {
    name: string
    code: string
    name_eng: string
  }
  geometry: {
    type: string
    coordinates: number[][][]
  }
}

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'regionChange', region: string, selected: boolean): void
}>()

const hoveredRegion = ref<string | null>(null)
const geoData = computed(() => jejuGeoJson.features as GeoFeature[])
const selectedRegions = computed(() => props.modelValue)

// SVG 크기
const svgWidth = 800
const svgHeight = 500
const padding = 40

// 경계 계산
const bounds = computed(() => {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity

  geoData.value.forEach(feature => {
    feature.geometry.coordinates[0].forEach(coord => {
      minX = Math.min(minX, coord[0])
      maxX = Math.max(maxX, coord[0])
      minY = Math.min(minY, coord[1])
      maxY = Math.max(maxY, coord[1])
    })
  })

  return { minX, maxX, minY, maxY }
})

// 경도/위도를 SVG 좌표로 변환
function toSvgCoords(lon: number, lat: number): [number, number] {
  const b = bounds.value
  const scaleX = (svgWidth - padding * 2) / (b.maxX - b.minX)
  const scaleY = (svgHeight - padding * 2) / (b.maxY - b.minY)
  const scale = Math.min(scaleX, scaleY)

  const offsetX = (svgWidth - (b.maxX - b.minX) * scale) / 2
  const offsetY = (svgHeight - (b.maxY - b.minY) * scale) / 2

  const x = (lon - b.minX) * scale + offsetX
  // Y축 뒤집기 (지도는 북쪽이 위)
  const y = svgHeight - ((lat - b.minY) * scale + offsetY)

  return [x, y]
}

// GeoJSON feature를 SVG path로 변환
function getPath(feature: GeoFeature): string {
  const coords = feature.geometry.coordinates[0]
  let path = ''

  coords.forEach((coord, i) => {
    const [x, y] = toSvgCoords(coord[0], coord[1])
    path += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`
  })

  return path + ' Z'
}

// 라벨 위치 (중심점)
function getLabelPosition(feature: GeoFeature): [number, number] {
  const coords = feature.geometry.coordinates[0]
  let sumX = 0, sumY = 0

  coords.forEach(coord => {
    sumX += coord[0]
    sumY += coord[1]
  })

  const centerLon = sumX / coords.length
  const centerLat = sumY / coords.length

  return toSvgCoords(centerLon, centerLat)
}

function isSelected(region: string): boolean {
  return props.modelValue.includes(region)
}

function toggleRegion(region: string) {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(region)

  if (index > -1) {
    newValue.splice(index, 1)
    emit('update:modelValue', newValue)
    emit('regionChange', region, false)
  } else {
    newValue.push(region)
    emit('update:modelValue', newValue)
    emit('regionChange', region, true)
  }
}
</script>

<style scoped>
.jeju-map-wrapper {
  width: 100%;
  max-width: 850px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: hidden;
}

.jeju-map-container {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  background: linear-gradient(180deg, #e1f5fe 0%, #b3e5fc 100%);
}

.jeju-svg {
  width: 100%;
  height: auto;
  display: block;
}

.region-path {
  fill: url(#regionGrad);
  stroke: #66bb6a;
  stroke-width: 2;
  cursor: pointer;
  transition: all 0.2s ease;
  filter: url(#shadow);
}

.region-path:hover,
.region-path.hovered {
  fill: url(#hoverGrad);
  stroke: #26c6da;
  stroke-width: 3;
}

.region-path.selected {
  fill: url(#selectedGrad);
  stroke: #00838f;
  stroke-width: 3;
}

.region-label {
  font-size: 11px;
  font-weight: 600;
  fill: #37474f;
  text-anchor: middle;
  dominant-baseline: middle;
  pointer-events: none;
  paint-order: stroke;
  stroke: white;
  stroke-width: 3px;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.region-label.label-selected {
  fill: white;
  stroke: #00838f;
  stroke-width: 3px;
  font-weight: 700;
}

.compass-text {
  font-size: 14px;
  font-weight: 700;
  fill: #e53935;
  text-anchor: middle;
}

/* 선택된 지역 카드 */
.selected-card {
  margin-top: 20px;
  background: white;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  height: 110px;
  box-sizing: border-box;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-content {
  height: 50px;
  overflow-y: auto;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #263238;
}

.card-icon {
  font-size: 20px;
}

.card-badge {
  padding: 6px 12px;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
  color: #00838f;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  min-width: 70px;
  text-align: center;
}

.selected-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #26c6da 0%, #00acc1 100%);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 3px 10px rgba(0, 172, 193, 0.3);
}

.chip:hover {
  background: linear-gradient(135deg, #00bcd4 0%, #00838f 100%);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 172, 193, 0.4);
}

.chip-remove {
  font-size: 18px;
  font-weight: 400;
  opacity: 0.8;
}

.chip:hover .chip-remove {
  opacity: 1;
}

.empty-state {
  text-align: center;
  padding: 12px 0;
  color: #90a4ae;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}
</style>
