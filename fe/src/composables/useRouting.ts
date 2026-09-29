import { useRoutingApi } from '@/composables/api/useRoutingApi';
import type { ApiResult } from '@/types/api';
import type {
  RawInputData,
  RoutingResponse,
  ParsedRoute,
  RoutingPlace,
} from '@/types/api/routing.dto';
import { convertTimeStrToMinutes } from '@/utils/date';
import type { Coordinates2D } from '@/types/common';
import { useUserStore } from '@/store/user';

export function useRouting() {
  const { fetchRawRoute, isLoading, error } = useRoutingApi();
  const userStore = useUserStore();

  /** 카테고리 매핑: DB 카테고리 → TripScheduler 카테고리 */
  function mapCategoryForTripScheduler(dbCategory: string): string {
    const categoryMapping: Record<string, string> = {
      'hotel': 'accommodation',
      'accommodation': 'accommodation',
      'tour': 'landmark',
      'tourist': 'landmark',
      'landmark': 'landmark',
      'cafe': 'cafe',
      'restaurant': 'restaurant',
      'transport': 'transport',
      'unknown': 'landmark'  // unknown도 landmark로 매핑
    };

    const mapped = categoryMapping[dbCategory.toLowerCase()];  // 소문자로 변환해서 매칭
    if (!mapped) {
      console.warn(`[mapCategoryForTripScheduler] Unknown category: ${dbCategory}, using 'landmark' as default`);
      return 'landmark';
    }
    return mapped;
  }

  /** 카테고리별 기본 service_time 반환 */
  function getDefaultServiceTime(category: string): number {
    const defaults: Record<string, number> = {
      'transport': 30,
      'restaurant': 60,
      'cafe': 45,
      'landmark': 90,
      'accommodation': 20
    };
    return defaults[category] || 60;
  }

  /** 카테고리별 기본 영업시간 반환 */
  function getDefaultHours(category: string): { open: string; close: string } {
    const defaults: Record<string, { open: string; close: string }> = {
      'transport': { open: '00:00', close: '23:59' },
      'restaurant': { open: '11:00', close: '21:00' },
      'cafe': { open: '09:00', close: '20:00' },
      'landmark': { open: '09:00', close: '18:00' },
      'accommodation': { open: '00:00', close: '23:00' }
    };
    return defaults[category] || { open: '09:00', close: '18:00' };
  }

  /** 1) 사용자 입력 로우 → trip-planner 요청 DTO */
  function buildRawRequest(input: RawInputData, currentDay?: string): any {
    console.info("Building trip-planner request with input:", input);

    // UserStore에서 실제 여행 날짜 정보 가져오기
    const startDate = userStore.state.startDate;
    const tripDays = userStore.state.tripDays;

    // 날짜 키들을 정렬하여 첫째 날과 마지막 날 확인
    const dayKeys = Object.keys(input.placesByDay).sort();
    console.info("Available day keys:", dayKeys);

    const firstDayIndex = dayKeys[0];
    console.info(`First day index from keys: ${firstDayIndex}`);

    // 현재 처리 중인 날짜 인덱스
    const targetDayIndex = currentDay || firstDayIndex;
    console.info(`Target day index: ${targetDayIndex}`);

    // 인덱스를 실제 날짜로 변환
    const dayIndexNum = parseInt(targetDayIndex);
    const actualDate = new Date(startDate);
    actualDate.setDate(actualDate.getDate() + dayIndexNum);
    const actualDateStr = actualDate.toISOString().split('T')[0];

    // 현재 날짜가 첫째 날인지, 마지막 날인지 확인 (전체 여행 기준)
    const isFirstDay = dayIndexNum === 0;
    const isLastDay = dayIndexNum === (tripDays - 1);

    console.info(`Processing day: ${targetDayIndex} -> actual date: ${actualDateStr}`);
    console.info(`Total trip days: ${tripDays}`);
    console.info(`is_first_day: ${isFirstDay}, is_last_day: ${isLastDay}`);

    // 해당 날짜의 장소들만 places 배열에 포함
    const places: any[] = [];
    let placeId = 1;

    const dayPlaces = input.placesByDay[targetDayIndex] || [];
    dayPlaces.forEach((place) => {
      // 좌표 검증 - 좌표가 없으면 건너뛰기
      if (!place.coord?.lng || !place.coord?.lat) {
        console.warn(`[buildRawRequest] Place ${place.name} has no coordinates, skipping`);
        return;
      }

      const mappedCategory = mapCategoryForTripScheduler(place.category || "unknown");
      const defaultHours = getDefaultHours(mappedCategory);

      places.push({
        id: placeId++,
        name: place.name,
        x_cord: place.coord.lng,  // ✅ || 0 제거
        y_cord: place.coord.lat,
        service_time: place.serviceMinutes ?? getDefaultServiceTime(mappedCategory),  // ✅ 카테고리별 기본값
        category: mappedCategory,
        open_time: place.openTime || defaultHours.open,  // ✅ 기본값 사용
        close_time: place.closeTime || defaultHours.close,
        tags: [],
        is_mandatory: mappedCategory === 'transport',  // ✅ Transport는 필수
        closed_days: [],
        break_time: []
      });
    });

    return {
      places,
      user: {
        start_time: "09:00",
        end_time: "18:00",
        travel_style: "normal",
        meal_time_preferences: {  // ✅ 추가
          breakfast: ["08:00", "09:00"],
          lunch: ["12:00", "13:30"],
          dinner: ["18:00", "19:30"]
        }
      },
      day_info: {
        type: "normal",
        is_first_day: isFirstDay,
        is_last_day: isLastDay,
        date: actualDateStr,
        weekday: actualDate.toLocaleDateString('ko-KR', { weekday: 'long' })
      },
      use_mock: false
    };
  }

  /** 2) trip-planner 응답 → 내부 도메인 형태로 변환 */
  function mapRawToInternal(raw: any, dayIndex: string): RoutingResponse {  // ✅ dayIndex 파라미터 추가
    console.info(`Mapping trip-planner response to internal format for day ${dayIndex}:`, raw);

    const placesByDay: RoutingResponse['placesByDay'] = {};

    if (raw.visits && Array.isArray(raw.visits)) {
      // dayIndex 사용 (항상 "0"이 아님)
      const dayNum = parseInt(dayIndex, 10);
      placesByDay[dayNum] = raw.visits.map((visit: any) => ({
        name: visit.place || visit.name || 'Unknown',
        address: visit.address || '',
        category: visit.category || 'unknown',
        arrival: visit.arrival_str || visit.arrival || '',
        departure: visit.departure_str || visit.departure || '',
        serviceMinutes: visit.stay_duration ? convertTimeStrToMinutes(visit.stay_duration) : 60,
        coord: {
          lng: visit.x_cord || visit.lng || 0,
          lat: visit.y_cord || visit.lat || 0
        },
      }));
    }

    const path: Coordinates2D[][] = raw.path ? raw.path.map((segment: any) =>
      segment.map(([lng, lat]: [number, number]) => ({ lng, lat }))
    ) : [];

    return { placesByDay, path };
  }

  /** 3) 전체 흐름: 입력 → RAW 요청 → RAW 응답 → 내부 형변환 → 파싱된 결과 */
  async function getParsedRoute(input: RawInputData): Promise<ApiResult<ParsedRoute[]>> {
    console.info("Fetching raw route data with input:", input);

    const dayKeys = Object.keys(input.placesByDay).sort();
    const allParsedRoutes: ParsedRoute[] = [];

    // 각 날짜별로 순차적으로 처리
    for (const day of dayKeys) {
      console.info(`Processing day: ${day}`);

      const rawReq = buildRawRequest(input, day);
      const rawResult = await fetchRawRoute(rawReq);

      if (!rawResult.success || !rawResult.data) {
        console.error(`Error fetching raw route data for day ${day}:`, rawResult.error);
        return { success: false, data: null, error: rawResult.error };
      }

      const internal = mapRawToInternal(rawResult.data, day);  
      console.info(`Internal data for day ${day}:`, internal);

      const hasAnyPlaces = Object.values(internal.placesByDay).some((places) => places.length > 0);

      if (!hasAnyPlaces) {
        console.warn(`[getParsedRoute] No valid places found in routing response for day ${day}.`);
        continue;
      }

      // 이 날짜의 결과를 파싱
      const dayNum = parseInt(day, 10);
      const places = internal.placesByDay[dayNum] || [];  
      const path = internal.path;

      if (path.length > 0) {
        console.info(`Path for Day ${day}:`);
        path.forEach((segment, segmentIndex) => {
          if (Array.isArray(segment)) {
            console.info(`  Segment ${segmentIndex + 1} has ${segment.length} Coordinates2D objects`);
          } else {
            console.warn(`  Segment ${segmentIndex + 1} is an invalid format`);
          }
        });
      }

      allParsedRoutes.push({
        day,
        places: places.map((p: RoutingPlace) => {
          return {
            name: p.name,
            address: p.address,
            category: p.category ?? 'unknown',
            arrival: p.arrival || '',
            departure: p.departure || '',
            serviceMinutes: p.serviceMinutes,
            coord: {
              lat: p.coord.lat,
              lng: p.coord.lng,
            },
          };
        }),
        path,
      });
    }

    return { success: true, data: allParsedRoutes, error: null };
  }

  return { getParsedRoute, isLoading, error };
}