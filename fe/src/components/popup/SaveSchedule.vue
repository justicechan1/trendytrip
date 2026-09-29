<template>
  <v-container>
    <!-- 🗓️ 전체 카드 -->
    <v-card class="pa-6 main-card" elevation="6">
      <!-- 여행 정보 -->
      <v-card-title class="text-h5 mb-4">✈️ 여행 정보</v-card-title>
      <v-card-text class="text-left mb-6">
        <h2>📍 지역: {{ userStore.state.area }}</h2>
        <h2>
          📅 여행 기간: {{ formattedStartDate }} ~ {{ formattedEndDate }}
          ({{ userStore.state.tripDays }}일)
        </h2>
      </v-card-text>

      <!-- 테스트 버튼 -->
      <v-card-actions>
        <v-btn color="primary" @click="loadItineraryData" :loading="isLoading">
          🔄 상세 정보 불러오기
        </v-btn>
      </v-card-actions>

      <!-- Day Timeline -->
      <v-timeline align="center" direction="horizontal" class="mb-6">
        <v-timeline-item
          v-for="day in userStore.state.tripDays"
          :key="day"
          :dot-color="dayColors[day]"
        >
          <v-btn
            :color="selectedDay === day ? dayColors[day] : '#000000'"
            variant="tonal"
            @click="selectDay(day)"
          >
            📅 Day {{ day }}
          </v-btn>
        </v-timeline-item>
      </v-timeline>

      <!-- 선택된 Day의 장소들 -->
      <v-row
        v-if="selectedDay && selectedPlaces.length"
        class="places-grid"
        dense
        justify="center"
      >
        <v-col
          v-for="(place, index) in selectedPlaces"
          :key="index"
          cols="12"
          sm="6"
          md="4"
        >
          <v-card class="pa-4 rounded-lg elevation-2 place-card">
            <v-card-title class="text-h6 mb-2">📍 {{ place.name }}</v-card-title>
            <v-card-subtitle class="mb-2">🏷️ {{ place.category }}</v-card-subtitle>

            <v-card-text class="text-left mb-2">
              <p>📍 <strong>주소:</strong> {{ place.address }}</p>
              <p>🕒 <strong>영업시간:</strong> {{ place.open_time }} - {{ place.close_time }}</p>
              <p>✨ <strong>편의시설:</strong> {{ place.convenience.join(', ') }}</p>
              <p>⏱️ <strong>체류시간:</strong> {{ place.service_time }}분</p>
              <p>🚶 <strong>도착:</strong> {{ place.arrival_str }}</p>
              <p>🚗 <strong>출발:</strong> {{ place.departure_str }}</p>
              <p>📝 <strong>설명:</strong> {{ place.description }}</p>
            </v-card-text>

            <!-- 이미지 가로 스크롤 -->
            <div class="image-scroll-container">
              <v-img
                v-for="(img, i) in place.image_urls"
                :key="i"
                :src="img"
                height="200"
                contain
                class="rounded-lg"
                style="min-width: 300px; margin-right: 8px;"
              />
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { parseISO, format } from 'date-fns'
import { ko } from 'date-fns/locale'
import type { ItineraryPlaceResponse } from '@/types/api/trip'
import { useUserStore } from '@/store/user'
import { useItineraryStore } from '@/store/itinerary'
import { useItineraryApi } from '@/composables/api/useItineraryApi'

const userStore = useUserStore()
const itineraryStore = useItineraryStore()
const { fetchItinerary, isLoading } = useItineraryApi()

// Day별 장소 데이터
const placesByDay = ref<Record<number, ItineraryPlaceResponse[]>>({})

// 선택된 Day
const selectedDay = ref<number | null>(null)

// 랜덤 색상 생성
function randomColor() {
  const letters = '0123456789ABCDEF'
  let color = '#'
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)]
  }
  return color
}

// Day별 랜덤 색상
const dayColors = computed(() => {
  const colors: Record<number, string> = {}
  for (let day = 1; day <= userStore.state.tripDays; day++) {
    colors[day] = randomColor()
  }
  return colors
})

// 선택된 Day의 장소 (1-based를 0-based로 변환)
const selectedPlaces = computed(() => {
  if (!selectedDay.value) return []

  const dayIndex = selectedDay.value - 1  // 1 → 0, 2 → 1, 3 → 2
  console.log('[SaveSchedule] selectedDay:', selectedDay.value, '→ dayIndex:', dayIndex)
  console.log('[SaveSchedule] placesByDay keys:', Object.keys(placesByDay.value))
  console.log('[SaveSchedule] placesByDay[dayIndex]:', placesByDay.value[dayIndex])

  return placesByDay.value[dayIndex] ?? []
})

// 타임라인 버튼 클릭
function selectDay(day: number) {
  selectedDay.value = day
}

// 날짜 포맷 헬퍼
const formattedStartDate = computed(() => {
  const startDate = userStore.state.startDate
  return startDate && !isNaN(Date.parse(startDate))
    ? format(parseISO(startDate), 'yyyy년 MM월 dd일', { locale: ko })
    : '시작일 정보 없음'
})

const formattedEndDate = computed(() => {
  const endDate = userStore.state.endDate
  return endDate && !isNaN(Date.parse(endDate))
    ? format(parseISO(endDate), 'yyyy년 MM월 dd일', { locale: ko })
    : '종료일 정보 없음'
})

// API 호출 함수 (재사용 가능)
async function loadItineraryData() {
  const current = itineraryStore.current
  if (!current?.placesByDay) {
    console.warn('[SaveSchedule] placesByDay가 없습니다')
    alert('⚠️ 여정 데이터가 없습니다. 먼저 여행 일정을 생성해주세요.')
    return
  }

  // ItineraryRequest 형식으로 변환
  const places_by_day: Record<string, any[]> = {}

  Object.entries(current.placesByDay).forEach(([dayStr, places]) => {
    places_by_day[dayStr] = places.map(p => ({
      name: p.name,
      arrival_str: p.arrival || '09:00',
      departure_str: p.departure || '10:00',
      service_time: p.serviceMinutes || 60
    }))
  })

  console.log('[SaveSchedule] API 요청 데이터:', { places_by_day })

  // API 호출
  const result = await fetchItinerary({ places_by_day })

  if (result.success && result.data) {
    // 응답 데이터를 placesByDay에 저장
    placesByDay.value = Object.entries(result.data.places_by_day).reduce((acc, [day, places]) => {
      acc[parseInt(day)] = places
      return acc
    }, {} as Record<number, ItineraryPlaceResponse[]>)

    console.log('[SaveSchedule] API 응답 데이터:', placesByDay.value)

    // 첫 번째 Day 자동 선택
    if (userStore.state.tripDays > 0) {
      selectedDay.value = 1
    }

    alert('✅ 상세 정보를 성공적으로 불러왔습니다!')
  } else {
    console.error('[SaveSchedule] API 호출 실패:', result.error)
    alert('❌ API 호출 실패: ' + (result.error || '알 수 없는 오류'))
  }
}

// 컴포넌트 마운트 시 자동 호출
onMounted(() => {
  loadItineraryData()
})
</script>

<style scoped>
.text-left {
  text-align: left;
}

/* 전체 카드 테두리 */
.main-card {
  border: 2px solid #00BFFF;
  background-color: rgb(249, 251, 252);
}

/* 각 장소 카드 테두리 */
.place-card {
  background-color: white;
  border: 2px solid #00BFFF;
}

/* 카드 내부 이미지 가로 스크롤 */
.image-scroll-container {
  display: flex;
  overflow-x: auto;
  gap: 8px;
  padding-bottom: 4px;
}
.image-scroll-container::-webkit-scrollbar {
  height: 6px;
}
.image-scroll-container::-webkit-scrollbar-thumb {
  background-color: rgba(0,0,0,0.3);
  border-radius: 3px;
}

/* v-row grid gap 조정 */
.places-grid {
  row-gap: 16px;
  column-gap: 16px;
}
</style>
