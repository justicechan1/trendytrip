<template>
  <div class="time-section">
    <div class="section-title center-text">
      <p>어디서 여행을 시작하시나요? 숙소도 예약하셨다구요?</p>
      <h3>🏕️ 여행 장소와 숙소를 입력해주세요</h3>
    </div>

    <div class="section-content">
      <!-- 출발 정보 -->
      <div class="input-card">
        <h3>✈️ 출발 장소 및 시간 입력</h3>
        <p>{{ userStore.state.startDate }}</p>
        <form class="radio-group">
          <label><input v-model="startPlace" type="radio" value="제주국제공항" /> 제주국제공항</label>
          <label><input v-model="startPlace" type="radio" value="제주국제여객터미널" /> 제주국제여객터미널</label>
        </form>
        <input v-model="startTime" type="time" class="text-input" />
      </div>

      <!-- 도착 정보 -->
      <div class="input-card">
        <h3>✈️ 마지막 장소 및 시간 입력</h3>
        <p>{{ userStore.state.endDate }}</p>
        <form class="radio-group">
          <label><input v-model="endPlace" type="radio" value="제주국제공항" /> 제주국제공항</label>
          <label><input v-model="endPlace" type="radio" value="제주국제여객터미널" /> 제주국제여객터미널</label>
        </form>
        <input v-model="endTime" type="time" class="text-input" />
      </div>

    </div>

    <footer class="section-footer flex-between">
      <button class="button-base button-prev" :disabled="isSubmitting" @click="emit('prev')">이전</button>
      <button class="button-base button-next" :disabled="isSubmitting" @click="handleConfirm">
        {{ isSubmitting ? '생성 중...' : '확인' }}
      </button>
    </footer>

    <!-- 중복 클릭 방지: 요청 처리 중엔 화면을 덮어 확인 버튼을 못 누르게 함 -->
    <div v-if="isSubmitting" class="loading-overlay">
      <div class="spinner"></div>
      <p>여행 일정을 생성하고 있어요...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { v4 as uuidv4 } from 'uuid';
import { useUserStore } from '@/store/user';
import { useItineraryStore } from '@/store/itinerary';
import { useItinerary } from '@/composables/useItinerary';
import axios from 'axios';
import { BACKEND_URL, JEJU_REGION_CODE_MAP } from '@/utils/constants';

import type { ItineraryPostBody } from '@/types/api/itinerary.dto';
import type { DayList } from '@/types/common';
import type { ItineraryPlace } from '@/types/domain/itinerary';

const emit = defineEmits<{
  (e: 'prev'): void;
}>();

const router = useRouter();
const userStore = useUserStore();
const itineraryStore = useItineraryStore();
const { createItinerary } = useItinerary();

// 기본 상태 초기화
const startPlace = ref(userStore.state.startPlace || '');
const startTime = ref(userStore.state.startTime || '');
const endPlace = ref(userStore.state.endPlace || '');
const endTime = ref(userStore.state.endTime || '');
const accommodationName = ref(userStore.state.accommodationName || '');
const selectedDay = ref<number | null>(userStore.state.accommodationDay ?? null);
const isSubmitting = ref(false);

// 장소 이름으로 백엔드에서 상세 정보 가져오기
async function fetchPlaceDetails(placeName: string): Promise<ItineraryPlace | null> {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/places/select_place?name=${encodeURIComponent(placeName)}`);
    const place = response.data.places;

    return {
      name: place.name,
      category: place.category,
      description: place.description || '',
      coord: {
        lat: place.y_cord,
        lng: place.x_cord
      },
      address: place.address || '',
      openTime: place.open_time,
      closeTime: place.close_time,
      images: place.image_urls || [],
      conveniences: place.convenience || [],
      arrival: '',
      departure: '',
      serviceMinutes: 0,
    };
  } catch (error) {
    console.error(`Failed to fetch place details for ${placeName}:`, error);
    return null;
  }
}

function saveToUserStore() {
  userStore.setStartPlace(startPlace.value);
  userStore.setStartTime(startTime.value);
  userStore.setEndPlace(endPlace.value);
  userStore.setEndTime(endTime.value);
  userStore.setAccommodationName(accommodationName.value);
  userStore.setAccommodationDay(selectedDay.value);
}

async function handleConfirm() {
  if (isSubmitting.value) return; // 중복 클릭 방지
  isSubmitting.value = true;
  try {
    await submitTrip();
  } finally {
    isSubmitting.value = false;
  }
}

async function submitTrip() {
  saveToUserStore();

  const uid = uuidv4();
  userStore.setUserId(uid);
  itineraryStore.setUserId(uid);

  // 출발지와 도착지의 상세 정보를 백엔드에서 가져오기
  console.log('출발지 상세 정보 가져오는 중:', userStore.state.startPlace);
  const startPlaceDetails = await fetchPlaceDetails(userStore.state.startPlace);

  console.log('도착지 상세 정보 가져오는 중:', userStore.state.endPlace);
  const endPlaceDetails = await fetchPlaceDetails(userStore.state.endPlace);

  if (!startPlaceDetails || !endPlaceDetails) {
    alert('출발지 또는 도착지 정보를 가져올 수 없습니다.');
    return;
  }

  const placesByDay: DayList<ItineraryPlace> = {
    0: [startPlaceDetails],
  };

  // 숙소 정보가 있으면 추가 (이것도 나중에 상세 정보로 변경 필요)
  if (userStore.state.accommodationDay !== null && userStore.state.accommodationName) {
    const day = userStore.state.accommodationDay;
    placesByDay[day] = placesByDay[day] || [];

    // 숙소도 상세 정보 가져오기
    const accommodationDetails = await fetchPlaceDetails(userStore.state.accommodationName);
    if (accommodationDetails) {
      placesByDay[day].push(accommodationDetails);
    } else {
      // 숙소 정보를 가져올 수 없으면 기본 구조로 추가
      placesByDay[day].push({
        name: userStore.state.accommodationName,
        category: 'hotel',
        description: '',
        coord: { lat: 0, lng: 0 },
        address: '',
        openTime: '00:00',
        closeTime: '23:59',
        images: [],
        conveniences: [],
        arrival: '',
        departure: '',
        serviceMinutes: 60,
      });
    }
  }

  const lastDay = userStore.state.tripDays - 1;
  placesByDay[lastDay] = placesByDay[lastDay] || [];
  placesByDay[lastDay].push(endPlaceDetails);

  // 지역 코드 변환
  const dailyLocations = userStore.state.jeju_area
    .map(area => JEJU_REGION_CODE_MAP[area])
    .filter(code => code !== undefined);

  const payload: ItineraryPostBody = {
    date: {
      userId: uid,
      startDate: userStore.state.startDate,
      endDate: userStore.state.endDate,
      arrivalTime: userStore.state.startTime,
      departureTime: userStore.state.endTime,
      startPlace: userStore.state.startPlace,
      endPlace: userStore.state.endPlace,
    },
    user: {
      startTime: userStore.state.startTime || '08:00',
      endTime: userStore.state.endTime || '20:00',
      travelStyle: userStore.state.tripStyle || 'relaxing',
      meals: {
        breakfast: ['08:00', '09:00'],
        lunch: ['11:00', '12:00'],
        dinner: ['18:00', '19:00'],
      },
      tags: userStore.state.tags,
    },
    placesByDay,
    dailyLocations: dailyLocations.length > 0 ? dailyLocations : undefined,
  };

  console.log('[TimeStep] ===== API 호출 시작 =====');
  console.log('[TimeStep] payload:', JSON.stringify(payload, null, 2));

  const result = await createItinerary(payload);

  console.log('[TimeStep] ===== API 호출 완료 =====');
  console.log('[TimeStep] result:', result);
  console.log('[TimeStep] result.success:', result.success);
  console.log('[TimeStep] result.data:', result.data);
  console.log('[TimeStep] result.error:', result.error);

  if (result.success && result.data && Object.keys(result.data.placesByDay).length > 0) {
    console.log('[TimeStep] ===== addItinerary 호출 직전 =====');
    console.log('[TimeStep] uid:', uid);
    console.log('[TimeStep] result.data:', result.data);

    itineraryStore.addItinerary(uid, result.data);
    itineraryStore.selectItinerary(uid);

    console.info('Timestep 완료 후 디버그');
    userStore.printDebug();
    itineraryStore.printDebug();

    router.push('/map');
  } else {
    console.error('[TimeStep] 일정 생성 실패');
    alert('일정 생성에 실패했습니다.');
  }
}
</script>

<style scoped>
.time-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 10;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #b2ebf2;
  border-top-color: #00acc1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.button-base:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.section-title {
  padding: 1rem 0;
  flex-shrink: 0;
}

.section-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-card {
  padding: 1.5rem;
  border: 1px solid #e0f0f5;
  border-radius: 12px;
  background-color: #f9fcff;
  box-shadow: 0 2px 8px rgba(0, 188, 212, 0.15);
}

.radio-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin: 1rem 0;
}

.day-select {
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
