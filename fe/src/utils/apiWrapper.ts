// utils/apiWrapper.ts

import type { ItineraryPostBody, ItineraryResponse, PlaceSummary } from '@/types/api/itinerary.dto.ts'
import type { DayList } from '@/types/common.ts'
import type { RawInitResponse } from '@/types/api/raw.ts'

type RawPlace = {
  name: string;
  x_cord: number;
  y_cord: number;
  category: string;
};

export type RawItinerary = {
  places_by_day: Record<string, RawPlace[]>;
};

export function wrapItineraryPayload(payload: ItineraryPostBody): any {

  const requestBody: any = {
    date: {
      user_id: payload.date.userId,
      start_date: payload.date.startDate,
      end_date: payload.date.endDate,
      arrival_time: payload.date.arrivalTime,
      departure_time: payload.date.departureTime,
      start_place: payload.date.startPlace,
      end_place: payload.date.endPlace,
    },
    user: {
      start_time: payload.user.startTime,
      end_time: payload.user.endTime,
      travel_style: payload.user.travelStyle,
      meal_time_preferences: {
        breakfast: payload.user.meals.breakfast,
        lunch: payload.user.meals.lunch,
        dinner: payload.user.meals.dinner,
      },
      tags: payload.user.tags.map(tag => tag.name),
    },
    places_by_day: Object.fromEntries(
      Object.entries(payload.placesByDay).map(([day, places]) => {
        const safeList = (places || []).map((place, i) => {
          if (!place || typeof place.name !== 'string') {
            console.warn(`[wrapItineraryPayload] ⚠️ invalid place at day=${day}, index=${i}:`, place);
            return { name: '' };
          }
          return { name: place.name };
        });

        // day를 1-base로 변환
        return [Number(day) + 1, safeList];
      })
    ),
  };

  // dailyLocations가 있으면 추가
  if (payload.dailyLocations && payload.dailyLocations.length > 0) {
    requestBody.daily_locations = payload.dailyLocations;
  }

  return requestBody;
}

// Init API 응답을 프론트엔드 형식으로 변환
export function wrapInitResponse(raw: RawInitResponse): ItineraryResponse {
  const placesByDay: DayList<PlaceSummary> = {};
  const pathsByDay: DayList<number[][][]> = {};

  console.log('[wrapInitResponse] raw.day_schedules:', raw.day_schedules);

  // day_schedules 배열을 순회
  for (const daySchedule of raw.day_schedules) {
    const dayIndexFromAPI = daySchedule.day; // 1-base (1, 2, 3)

    // dayIndex가 유효한 값인지 확인
    if (typeof dayIndexFromAPI !== 'number' || dayIndexFromAPI < 1) {
      console.warn(`[wrapInitResponse] 잘못된 dayIndex 발견: ${dayIndexFromAPI}`);
      continue;
    }

    // 1-base → 0-base 변환 (API Day 1 → 내부 Day 0)
    const dayIndex = dayIndexFromAPI - 1;

    // visits를 PlaceSummary로 변환
    placesByDay[dayIndex] = daySchedule.visits.map(visit => {
      // stay_duration을 분 단위로 변환
      const serviceMinutes = visit.stay_duration
        ? parseTimeToMinutes(visit.stay_duration)
        : 0;

      // 시간 데이터가 이미 문자열인지 확인하고, 아니면 문자열로 변환
      const arrivalStr = typeof visit.arrival_str === 'string'
        ? visit.arrival_str
        : String(visit.arrival_str || '')
      const departureStr = typeof visit.departure_str === 'string'
        ? visit.departure_str
        : String(visit.departure_str || '')

      return {
        name: visit.place,  // "place" 필드를 "name"으로 매핑
        coord: { lng: visit.x_cord, lat: visit.y_cord },
        category: visit.category,
        arrival: arrivalStr,    // 도착 시간
        departure: departureStr, // 출발 시간
        serviceMinutes,                 // 체류 시간 (분)
        travelTime: visit.travel_time,  // 이동 시간
        waitTime: visit.wait_time,      // 대기 시간
      };
    });

    // path 정보 추가
    if (daySchedule.path && daySchedule.path.length > 0) {
      pathsByDay[dayIndex] = daySchedule.path;
    }
  }

  console.log('[wrapInitResponse] placesByDay:', placesByDay);
  console.log('[wrapInitResponse] pathsByDay:', pathsByDay);

  return { placesByDay, pathsByDay };
}

// "HH:MM" 형식을 분 단위로 변환
function parseTimeToMinutes(timeStr: string): number {
  const parts = timeStr.split(':');
  if (parts.length !== 2) return 0;
  const hours = parseInt(parts[0], 10);
  const minutes = parseInt(parts[1], 10);
  return hours * 60 + minutes;
}

// 기존 함수 유지 (Routing API용)
export function wrapItineraryResponse(raw: RawItinerary): ItineraryResponse {
  const placesByDay: DayList<PlaceSummary> = {};

  for (const [key, places] of Object.entries(raw.places_by_day)) {
    const dayIndex = parseInt(key, 10) - 1;

    // dayIndex가 유효한 값인지 확인
    if (isNaN(dayIndex)) {
      console.warn(`[wrapItineraryResponse] 잘못된 dayIndex 발견: ${key}`);
      continue; // 잘못된 dayIndex는 건너뛰기
    }

    placesByDay[dayIndex] = places.map(place => ({
      name: place.name,
      coord: { lng: place.x_cord, lat: place.y_cord },
      category: place.category,
    }));
  }

  return { placesByDay };
}
