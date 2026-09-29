// src/stores/user/index.ts

import { defineStore } from 'pinia';
import { reactive, computed } from 'vue';
import type { UserState, UserPreferences } from '@/types/domain/user';
import type { Viewport, Hashtag, Category, ISODate, ISOTime } from '@/types/common';

export const useUserStore = defineStore('user', () => {
  const state = reactive<UserState>({
    id: '',
    area: '',
    startDate: '' as ISODate,
    endDate: '' as ISODate,
    tripDays: 0,
    startPlace: '',
    startTime: '' as ISOTime,
    endPlace: '',
    endTime: '' as ISOTime,
    selectedDates: [],
    accommodationName: '',
    accommodationDay: null,
    tags: [],
    category: '' as Category | '',
    tripStyle: '',  //여행 스타일
    jeju_area: [],  // 선택한 제주 읍면 지역
    viewport: null,
    preferences: null,
  });

  // 상태 판별 컴퓨티드
  const hasArea = computed(() => !!state.area);
  const hasTags = computed(() => state.tags.length > 0);
  const hasCategory = computed(() => !!state.category);
  const hasPreferences = computed(() => state.preferences !== null);

  // Mutations
  const setUserId = (id: string) => (state.id = id);
  const setArea = (area: string) => (state.area = area);
  const setTags = (tags: Hashtag[]) => (state.tags = tags);
  const setCategory = (category: Category) => (state.category = category);
  const setViewport = (viewport: Viewport | null) => (state.viewport = viewport);
  const setPreferences = (prefs: UserPreferences | null) => (state.preferences = prefs);
  const setStyle = (style: string) => (state.tripStyle = style);
  const setJejuAreas = (jeju_area: string[]) => (state.jeju_area = jeju_area);
  const setStartDate = (date: ISODate) => (state.startDate = date);
  const setEndDate = (date: ISODate) => (state.endDate = date);
  const setStartTime = (time: ISOTime) => (state.startTime = time);
  const setEndTime = (time: ISOTime) => (state.endTime = time);

  const setTripDays = (days: number) => (state.tripDays = days);
  const setSelectedDates = (dates: ISODate[]) => (state.selectedDates = dates);
  const setStartPlace = (place: string) => (state.startPlace = place);
  const setEndPlace = (place: string) => (state.endPlace = place);
  const setAccommodationName = (name: string) => (state.accommodationName = name);
  const setAccommodationDay = (day: number | null) => (state.accommodationDay = day);

  const resetAll = () => {
    state.area = '';
    state.tags = [];
    state.category = '';
    state.viewport = null;
    state.preferences = null;
  };

  function printDebug() {
    console.log('👤 User Store Debug Info 👤')
    console.log('----------------------------------')

    console.log('User ID:', state.id)
    console.log('Area:', state.area)
    console.log('Start Date:', state.startDate)
    console.log('End Date:', state.endDate)
    console.log('Trip Days:', state.tripDays)
    console.log('Selected Dates:', state.selectedDates.join(', '))
    console.log('Start Place:', state.startPlace)
    console.log('Start Time:', state.startTime)
    console.log('End Place:', state.endPlace)
    console.log('End Time:', state.endTime)
    console.log('Trip Style:', state.tripStyle)
    console.log('Jeju Areas:', state.jeju_area.length > 0 ? state.jeju_area.join(', ') : 'None')
    console.log('Selected tags:', state.tags.length > 0 ? state.tags.map(t => t.name).join(', ') : 'None')

    console.log('\n🏨 Accommodation:')
    console.log('Accommodation Name:', state.accommodationName)
    console.log('Accommodation Day:', state.accommodationDay)

    console.log('\n🏷 Tags:', state.tags.length > 0 ? state.tags.join(', ') : 'None')
    console.log('📂 Category:', state.category || 'None')

    console.log('\n🧭 Preferences:')
    if (state.preferences) {
      console.log(JSON.stringify(state.preferences, null, 2))
    } else {
      console.log('  None')
    }

    console.log('----------------------------------')
  }

  return {
    state,

    hasArea,
    hasTags,
    hasCategory,
    hasPreferences,

    setUserId,
    setArea,
    setTags,
    setCategory,
    setViewport,
    setPreferences,
    setStartDate,
    setEndDate,
    setStartTime,
    setEndTime,
    setTripDays,
    setSelectedDates,
    setStyle,
    setJejuAreas,
    setStartPlace,
    setEndPlace,
    setAccommodationName,
    setAccommodationDay,
    resetAll,
    printDebug
  };
});
