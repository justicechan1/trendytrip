<template>
  <nav class="side">
    <button @click="togglePopup('search')">🔍</button>
    <button @click="togglePopup('calendar')">📆</button>
    <button @click="togglePopup('save')">💾</button>

    <div class="popup-wrapper">
      <transition name="slide-popup">
        <component v-if="activeComponent" :is="activeComponent" class="popup-panel" @close="closePopups"
          @get-place-info="handleSelectPlace" />
      </transition>

      <transition name="slide-popup">
        <PopupContainer v-if="activeComponent" :mainComponent="activeComponent" :detail="selectedPlaceDetail"
          :showDetail="showDetailPopup" :on-close="closePopups" :on-close-detail="() => showDetailPopup = false"
          :on-select-place="handleSelectPlace" :on-add-place="handleAddPlace" />
      </transition>

    </div>
  </nav>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { usePopup } from '@/composables/usePopup';
import CalPop from '@/components/popup/CalendarPopup.vue';
import SearchPop from '@/components/popup/SearchPopup.vue';
import SavePop from '@/components/popup/SavePopup.vue';
import { usePlaceDetail } from '@/composables/usePlaceDetail';
import { useRouting } from '@/composables/useRouting';
import { useItineraryStore } from '@/store/itinerary';
import { useMapStore } from '@/store/map';

import type { PlaceDetail } from '@/types/domain/place';
import type { RoutingRequest } from '@/types/api/routing.dto';
import type { ItineraryPlace } from '@/types/domain/itinerary';
import type { PlaceSummary } from '@/types/api/itinerary.dto';
import type { PlaceSearchHit } from '@/types/api/place.dto';
import PopupContainer from '@/components/popup/PopupContainer.vue'

// ─── 팝업 상태 관리 ───────────────────────────
const {
  isCalendarPopupVisible,
  isSearchPopupVisible,
  isSavePopupVisible,
  togglePopup,
  closePopups,
} = usePopup();
const activeComponent = computed(() => {
  if (isCalendarPopupVisible.value) return CalPop;
  if (isSearchPopupVisible.value) return SearchPop;
  if (isSavePopupVisible.value) return SavePop;
  return null;
});
const mapStore = useMapStore()

// ─── 장소 상세 보기 ───────────────────────────
const { placeDetail, fetchPlaceDetail } = usePlaceDetail();
const selectedPlaceDetail = ref<PlaceDetail | null>(null);
const showDetailPopup = ref(false);

async function handleSelectPlace(hit: PlaceSearchHit) {
  console.debug('선택된 장소:', hit);

  // PlaceSearchHit에서 name을 사용하여 장소의 상세 정보를 가져옵니다.
  await fetchPlaceDetail({ name: hit.name });

  if (placeDetail.value) {
    selectedPlaceDetail.value = placeDetail.value;
    showDetailPopup.value = true;

    const { lng, lat } = placeDetail.value.coord;

    if (mapStore.map) {
      const markerPlace: PlaceSummary = {
        name: placeDetail.value.name,
        coord: { lng, lat },
        category: placeDetail.value.category ?? 'default',
      };

      mapStore.addPlaceMarker(markerPlace);
      mapStore.setZoom(16);
      mapStore.panTo(lat, lng);
    } else {
      console.warn("🚨 map.value가 아직 초기화되지 않았습니다.");
    }
  }
}

// ─── 장소 추가 & 경로 계산 ─────────────────────
async function handleAddPlace() {
  const itineraryStore = useItineraryStore();
  const { getParsedRoute } = useRouting();

  if (!selectedPlaceDetail.value) return;

  const day = itineraryStore.state.selectedDay;
  itineraryStore.printDebug();

  const newPlace: ItineraryPlace = {
    ...selectedPlaceDetail.value,
    arrival: '',
    departure: '',
    serviceMinutes: null,
  };

  // ─── 1. ‘current’ 및 ‘routingResult’ 상태 백업 ───
  const backupCurrentPlaces = [
    ...(itineraryStore.current?.placesByDay[day] ?? []),
  ];
  const backupRoutingPlaces = [
    ...(itineraryStore.state.routingResult.placesByDay[day] ?? []),
  ];
  const backupRoutingPath = [
    ...(itineraryStore.state.routingResult.path[day] ?? []),
  ];

  // ─── 2. 장소 추가 ───
  itineraryStore.addPlaceToCurrentDay(day, newPlace);

  // ─── 3. RoutingRequest 생성 ───
  const request: RoutingRequest | null =
    itineraryStore.generateRoutingRequestForSelectedDay();
  if (!request) {
    // “요청 생성 실패” 시 rollback
    if (itineraryStore.current) {
      // (A) current.placesByDay[day] → 완전히 재할당
      itineraryStore.current.placesByDay = {
        ...itineraryStore.current.placesByDay,
        [day]: [...backupCurrentPlaces],
      };
    }

    // (B) routingResult.placesByDay[day] → 완전 재할당
    itineraryStore.state.routingResult.placesByDay = {
      ...itineraryStore.state.routingResult.placesByDay,
      [day]: [...backupRoutingPlaces],
    };
    // (C) routingResult.path[day] → 완전 재할당
    const newPathObj = [...itineraryStore.state.routingResult.path];
    newPathObj[day] = [...backupRoutingPath];
    itineraryStore.state.routingResult.path = newPathObj;

    return;
  }

  // ─── 4. API 호출 ───
  const result = await getParsedRoute(request);

  const isValid =
    result.success === true &&
    Array.isArray(result.data) &&
    result.data.length > 0 &&
    result.data[0].places.length > 0 &&
    result.data[0].path.length > 0;

  if (isValid && result.data) {
    // ─── 5. 성공 시 store에 저장 ───
    itineraryStore.saveParsedRoutingResult(result.data);
  } else {
    // ─── 6. 실패 시 rollback ───
    console.warn(
      '[handleAddPlace] Empty or invalid routing result. Rolling back all changes.'
    );

    if (itineraryStore.current) {
      // (A) current.placesByDay[day] 완전 재할당
      itineraryStore.current.placesByDay = {
        ...itineraryStore.current.placesByDay,
        [day]: [...backupCurrentPlaces],
      };
    }

    // (B) routingResult.placesByDay[day] 완전 재할당
    itineraryStore.state.routingResult.placesByDay = {
      ...itineraryStore.state.routingResult.placesByDay,
      [day]: [...backupRoutingPlaces],
    };
    // (C) routingResult.path[day] 완전 재할당
    const newPathObj = [...itineraryStore.state.routingResult.path];
    newPathObj[day] = [...backupRoutingPath];
    itineraryStore.state.routingResult.path = newPathObj;
  }

  // ─── 7. UI 닫기 ───
  showDetailPopup.value = false;
  isCalendarPopupVisible.value = true;
}
</script>

<style scoped>
.side {
  position: absolute;
  top: 5%;
  left: 1vw;
  width: 60px;
  height: 80%;
  border: 2px solid skyblue;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  background: white;
  border-radius: 12px;
  padding: 12px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}

.side button {
  width: 40px;
  height: 40px;
  font-size: 24px;
  margin: 10px 0;
  background: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.side button:hover {
  background: #e0f6ff;
}

.popup-panel {
  position: absolute;
  left: calc(100% + 10px);
  top: 0;
}

.slide-popup-enter-active,
.slide-popup-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.slide-popup-enter-from,
.slide-popup-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-popup-enter-to,
.slide-popup-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
