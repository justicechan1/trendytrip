<template>
  <div class="popup-container">
    <header class="popup-header">
      <h2>{{ userStore.state.area }} 여행</h2>
      <p class="date-range">
        {{ formattedStartDate }} ~ {{ formattedEndDate }} (총 {{ userStore.state.tripDays }}일)
      </p>
      <label for="select-day" class="visually-hidden">일차 선택</label>
      <select id="select-day" v-model.number="selectedDay" class="select-day" aria-label="여행 일차 선택">
        <option v-for="n in userStore.state.tripDays" :key="n" :value="n - 1">
          Day {{ n }}
        </option>
      </select>
    </header>

    <article class="choose">
      <ItineraryTimeline v-if="currentVisits.length" :visits="currentVisits" @get-place-info="selectPlace" @delete-visit="handleDeleteVisit" />
      <p v-else>선택된 일차에 방문지가 없습니다.</p>
    </article>

    <footer>
      <button class="button-close" @click="emit('close')">
        닫기 ❌
      </button>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { computed, watch, defineEmits, onMounted } from 'vue'
import { parseISO, format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { useUserStore } from '@/store/user'
import { useItineraryStore } from '@/store/itinerary'
import { useMapStore } from '@/store/map'
import ItineraryTimeline from '@/components/common/ItineraryTimeline.vue'
import type { PlaceName } from '@/types/common'
import type { PlaceSearchHit } from '@/types/api/place.dto'
import { useRouting } from '@/composables/useRouting'


const emit = defineEmits<{
  (e: 'close'): void
  (e: 'get-place-info', place: PlaceSearchHit): void
}>()

const userStore = useUserStore()
const itineraryStore = useItineraryStore()
const mapStore = useMapStore()
const { getParsedRoute } = useRouting()

onMounted(() => {
  if (itineraryStore.state.selectedDay === undefined || itineraryStore.state.selectedDay === 0) {
    itineraryStore.updateSelectedDay(0);
  }
});

const selectedDay = computed<number>({
  get: () => {
    const day = itineraryStore.state.selectedDay;
    return day !== undefined ? day : 0; // 기본값 0 설정
  },
  set: (day) => {
    if (day !== undefined && day >= 0) {  // day가 undefined가 아니고 유효한 값인 경우만 처리
      itineraryStore.updateSelectedDay(day);
      updateMapWithNewDay(day);
    } else {
      console.error('Invalid day value:', day); // `undefined` 처리 방지
    }
  }
});

// 2) tripDays가 바뀔 때 selectedDay 유효 범위 체크
watch(
  () => userStore.state.tripDays,
  (days) => {
    if (itineraryStore.state.selectedDay > days) {
      console.warn('selectedDay가 tripDays를 초과하여 초기화됩니다.'); // 디버깅 로그 추가
      itineraryStore.updateSelectedDay(0);
    }
  },
  { immediate: true }
);

// 3) 현재 일차 데이터
const currentVisits = computed(() => {
  return itineraryStore.getProcessedPlaces(selectedDay.value).places;
});

// 4) 날짜 포맷 헬퍼
const formattedStartDate = computed(() => {
  const startDate = userStore.state.startDate;

  return startDate && !isNaN(Date.parse(startDate))
    ? format(parseISO(startDate), 'yyyy년 MM월 dd일', { locale: ko })
    : '시작일 정보 없음'; // 기본값 설정
});

const formattedEndDate = computed(() => {
  const endDate = userStore.state.endDate;

  return endDate && !isNaN(Date.parse(endDate))
    ? format(parseISO(endDate), 'yyyy년 MM월 dd일', { locale: ko })
    : '종료일 정보 없음'; // 기본값 설정
});

// 5) 장소 정보 요청 이벤트
function selectPlace(place: PlaceName) {
  const placeHit = {
    name: place
  }
  emit('get-place-info', placeHit);
}

// 지도 업데이트 함수: selectedDay가 바뀔 때마다 호출
function updateMapWithNewDay(day: number) {
  const { path, placesByDay } = itineraryStore.state.routingResult;

  console.info(`[updateMapWithNewDay] 선택된 일차: ${day}`);
  console.info('[updateMapWithNewDay] routingResult.path:', path);
  console.info('[updateMapWithNewDay] routingResult.placesByDay:', placesByDay);

  // 1. 기존 마커/선 삭제
  mapStore.clearMarkers();
  mapStore.clearPolylines();

  // 2. 경로(segment) 그리기
  const segments = path[day] || [];
  console.info(`[updateMapWithNewDay] segments for day ${day}:`, segments);
  console.info(`[updateMapWithNewDay] segments.length:`, segments.length);

  const colorPalette = ['#007aff', '#34c759', '#ff9500', '#ff3b30', '#5856d6'];

  segments.forEach((segment, index) => {
    console.info(`[updateMapWithNewDay] segment ${index}:`, segment, 'length:', segment.length);
    if (segment.length > 1) {
      // segment는 [[lng, lat], ...] 형식이므로 { lat, lng } 형식으로 변환
      const coords = (segment as unknown as number[][]).map((point) => ({
        lat: point[1],  // 두 번째 값이 lat
        lng: point[0]   // 첫 번째 값이 lng
      }));

      console.info(`[updateMapWithNewDay] converted coords ${index}:`, coords);

      mapStore.drawPolyline(coords, {
        strokeColor: colorPalette[index % colorPalette.length],
        strokeWeight: 4,
        zIndex: 1,
        segmentIndex: index,
      });
    }
  });

  if (segments.length === 0) {
    console.warn('[updateMapWithNewDay] 해당 일차의 경로가 없습니다.');
  }

  // 3. 장소 마커 추가
  const places = placesByDay[day] || [];
  places.forEach((place, index) => {
    mapStore.addPlaceMarker(place, index);
  });

  if (places.length === 0) {
    console.warn('[updateMapWithNewDay] 해당 일차에 방문할 장소가 없습니다.');
  }
}
//타임라인에서 온 삭제 이벤트 처리 (+ /schedule 호출)
async function handleDeleteVisit(index: number) {
  const day = selectedDay.value

  const currentId = itineraryStore.state.currentId
  if (!currentId) {
    console.warn('현재 선택된 일정이 없습니다.')
    return
  }

  const currentItinerary = itineraryStore.state.items[currentId]
  if (!currentItinerary || !currentItinerary.placesByDay[day]) {
    console.warn(`Day ${day}에 해당하는 장소 목록이 없습니다.`)
    return
  }

  const originalList = currentItinerary.placesByDay[day]
  const target = originalList[index]
  if (!target) return

  const ok = window.confirm(`'${target.name}' 방문지를 삭제할까요?`)
  if (!ok) return

  // ─── 1. 백업 만들어두기 ─────────────────────
  const backupCurrentPlaces = [...originalList]
  const backupRoutingPlaces = [
    ...(itineraryStore.state.routingResult.placesByDay[day] ?? []),
  ]
  const backupRoutingPath = [
    ...(itineraryStore.state.routingResult.path[day] ?? []),
  ]

  // ─── 2. 현재 일정에서 해당 장소 제거 ────────
  const newPlacesForDay = originalList.filter((_, i) => i !== index)

  // placesByDay를 통째로 새 객체로 할당 (반응성 보장)
  currentItinerary.placesByDay = {
    ...currentItinerary.placesByDay,
    [day]: newPlacesForDay,
  }

  // ─── 3. /schedule 호출에 쓸 요청 만들기 ─────
  const request = itineraryStore.generateRoutingRequestForSelectedDay()
  if (!request) {
    console.warn('[handleDeleteVisit] RoutingRequest 생성 실패, 롤백합니다.')

    // 롤백: 원래대로 되돌리기
    currentItinerary.placesByDay = {
      ...currentItinerary.placesByDay,
      [day]: [...backupCurrentPlaces],
    }
    itineraryStore.state.routingResult.placesByDay = {
      ...itineraryStore.state.routingResult.placesByDay,
      [day]: [...backupRoutingPlaces],
    }
    const pathCopy = [...itineraryStore.state.routingResult.path]
    pathCopy[day] = [...backupRoutingPath]
    itineraryStore.state.routingResult.path = pathCopy

    updateMapWithNewDay(day)
    return
  }

  // ─── 4. /schedule (getParsedRoute) 호출 ──────
  const result = await getParsedRoute(request)

  const isValid =
    result.success === true &&
    Array.isArray(result.data) &&
    result.data.length > 0 &&
    result.data[0].places.length > 0 &&
    result.data[0].path.length > 0

  if (isValid && result.data) {
    // ─── 5. 성공: 새 routingResult 저장 ────────
    itineraryStore.saveParsedRoutingResult(result.data)
  } else {
    // ─── 6. 실패: 전부 롤백 ───────────────────
    console.warn('[handleDeleteVisit] 경로 재계산 실패, 롤백합니다.')

    currentItinerary.placesByDay = {
      ...currentItinerary.placesByDay,
      [day]: [...backupCurrentPlaces],
    }
    itineraryStore.state.routingResult.placesByDay = {
      ...itineraryStore.state.routingResult.placesByDay,
      [day]: [...backupRoutingPlaces],
    }
    const pathCopy = [...itineraryStore.state.routingResult.path]
    pathCopy[day] = [...backupRoutingPath]
    itineraryStore.state.routingResult.path = pathCopy
  }

  // ─── 7. 최종적으로 지도 다시 그리기 ────────
  updateMapWithNewDay(day)
}

</script>

<style scoped>
@import "@/styles/popup.css";

/* 선택된 날짜 드롭다운 스타일 */
.select-day {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: #f9f9f9;
  cursor: pointer;
}

.select-day:hover {
  border-color: #888;
}

/* 중간 영역 */
article.choose {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-grow: 1;
  overflow-y: auto;
}

article.choose p {
  font-size: 1rem;
  color: #888;
  text-align: center;
}

/* 버튼 스타일 */
button {
  padding: 10px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  /* 버튼 크기를 100%로 통일 */
}

/* 경고 메시지 스타일 */
article.choose p {
  font-size: 1rem;
  color: #999;
  text-align: center;
  font-style: italic;
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 4px;
}
</style>
