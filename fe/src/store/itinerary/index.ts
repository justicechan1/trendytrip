import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import { format, parseISO } from 'date-fns'
import { ko } from 'date-fns/locale'
import type {
  InternalItinerary,
  ItineraryPlace,
} from '@/types/domain/itinerary'
import type {
  RoutingRequest,
  RoutingPlace,
  ParsedRoute
} from '@/types/api/routing.dto'
import type { ItineraryProcessedPlace } from '@/types/api/itinerary.dto'
import type { DayList, Coordinates2D } from '@/types/common'

export const useItineraryStore = defineStore('itinerary', () => {
  const state = reactive({
    items: {} as Record<string, InternalItinerary>,
    currentId: null as string | null,
    selectedDay: 0,
    userId: '',
    routingResult: {
      placesByDay: {} as DayList<RoutingPlace>,
      path: [] as Coordinates2D[][][],
    },
  })

  const current = computed(() =>
    state.currentId ? state.items[state.currentId] : null
  )

  const totalPlaces = computed(() =>
    current.value ? Object.values(current.value.placesByDay).flat().length : 0
  )

  function setUserId(id: string) {
    state.userId = id
  }

  function addItinerary(id: string, itin: InternalItinerary) {
    state.items = { ...state.items, [id]: itin }
    state.currentId = id

    console.log('[addItinerary] 저장되는 데이터:', itin)

    // Init API 데이터를 routingResult에도 저장하여 지도 렌더링에 사용
    if (itin.pathsByDay) {
      // pathsByDay는 { 0: [...], 1: [...] } 형태
      // routingResult.path는 [[...], [...]] 배열 형태여야 함
      const maxDay = Math.max(...Object.keys(itin.pathsByDay).map(Number))
      const pathArray: Coordinates2D[][][] = []

      for (let i = 0; i <= maxDay; i++) {
        pathArray[i] = itin.pathsByDay[i] || []
      }

      state.routingResult.path = pathArray
      console.log('[addItinerary] routingResult.path 설정:', state.routingResult.path)
    }

    state.routingResult.placesByDay = itin.placesByDay
    console.log('[addItinerary] routingResult.placesByDay 설정:', state.routingResult.placesByDay)
  }

  function selectItinerary(id: string) {
    if (state.items[id]) state.currentId = id
  }

  function removeItinerary(id: string) {
    const { [id]: _, ...rest } = state.items
    state.items = rest
    if (state.currentId === id) state.currentId = null
  }

  function reorderPlaces(day: number, newList: ItineraryPlace[]) {
    if (current.value) {
      current.value.placesByDay[day] = newList
    }
  }

  function generateRoutingRequestForSelectedDay(): RoutingRequest | null {
    if (!current.value) {
      console.warn('No current itinerary available.')
      return null
    }

    const day = state.selectedDay
    const places = current.value.placesByDay[day] ?? []
    if (places.length === 0) {
      console.warn(`No places found for day ${day}.`)
      return null
    }

    const routingRequest: RoutingRequest = {
      userId: state.userId,
      placesByDay: {
        [day]: places.map(p => ({
          name: p.name,
          serviceMinutes: p.serviceMinutes ?? null,
          coord: p.coord,
          category: p.category,
          openTime: p.openTime,
          closeTime: p.closeTime,
        })),
      },
    }

    return routingRequest
  }

  function updateSelectedDay(day: number) {
    state.selectedDay = day
  }

  function convertRoutingPlaceToItineraryPlace(rp: RoutingPlace): ItineraryPlace {
    return {
      name: rp.name,
      category: rp.category ?? 'unknown',
      address: rp.address ?? '',
      arrival: rp.arrival ?? '',
      departure: rp.departure ?? '',
      serviceMinutes: rp.serviceMinutes != null ? rp.serviceMinutes : 0,
      coord: rp.coord,
      openTime: '',
      closeTime: '',
      conveniences: [],
      images: [],
      description: '',
    }
  }

  // saveParsedRoutingResult: 여러 일차에 대한 path와 placesByDay를 병합하여 저장
  function saveParsedRoutingResult(data: ParsedRoute[]) {
    if (!current.value) {
      console.error('[saveParsedRoutingResult] current.value is null or undefined')
      return
    }

    const placesByDay = current.value.placesByDay ?? {}
    const newPlacesByDay: DayList<ItineraryPlace> = {}
    const newPathsByDay: DayList<Coordinates2D[][]> = {}

    data.forEach((parsedRoute) => {
      const dayIndex = parseInt(parsedRoute.day, 10)
      if (isNaN(dayIndex)) return

      // 장소 변환
      newPlacesByDay[dayIndex] = parsedRoute.places.map((p) =>
        convertRoutingPlaceToItineraryPlace({
          name: p.name,
          category: p.category,
          address: p.address,
          arrival: p.arrival,
          departure: p.departure,
          serviceMinutes: p.serviceMinutes,
          coord: { lng: p.coord.lng, lat: p.coord.lat },
        })
      )

      // 일자별 경로 저장
      // Routing API path는 Coordinates2D[][]이지만, Init API는 number[][][]
      // 형식을 맞추기 위해 변환
      if (parsedRoute.path && parsedRoute.path.length > 0) {
        const convertedPath = parsedRoute.path.map(segment =>
          segment.map(coord => [coord.lng, coord.lat])
        )
        newPathsByDay[dayIndex] = convertedPath as any
      }
    })

    // current.value에 병합
    current.value.placesByDay = {
      ...placesByDay,
      ...newPlacesByDay,
    }

    if (current.value.pathsByDay) {
      current.value.pathsByDay = {
        ...current.value.pathsByDay,
        ...newPathsByDay,
      }
    } else {
      current.value.pathsByDay = newPathsByDay
    }

    // routingResult에도 동일하게 저장 (Init API와 동일한 방식)
    state.routingResult.placesByDay = {
      ...state.routingResult.placesByDay,
      ...newPlacesByDay,
    }

    // path 배열 형식으로 변환
    const allPathsByDay = current.value.pathsByDay
    if (allPathsByDay) {
      const maxDay = Math.max(...Object.keys(allPathsByDay).map(Number))
      const pathArray: Coordinates2D[][][] = []

      for (let i = 0; i <= maxDay; i++) {
        pathArray[i] = allPathsByDay[i] || []
      }

      state.routingResult.path = pathArray
    }

    console.log('[saveParsedRoutingResult] 업데이트 완료')
    console.log('[saveParsedRoutingResult] current.value.placesByDay:', current.value.placesByDay)
    console.log('[saveParsedRoutingResult] current.value.pathsByDay:', current.value.pathsByDay)
    console.log('[saveParsedRoutingResult] routingResult:', state.routingResult)
  }

  function addPlaceToCurrentDay(day: number, place: ItineraryPlace) {
    if (!current.value) return
    current.value.placesByDay[day] = current.value.placesByDay[day] ?? []
    current.value.placesByDay[day].push(place)
  }

  function getProcessedPlaces(day: number): { day: number; places: ItineraryProcessedPlace[] } {
    const cur = current.value
    if (!cur?.placesByDay?.[day]) {
      return { day, places: [] }
    }

    console.log('[getProcessedPlaces] day:', day)
    console.log('[getProcessedPlaces] cur.placesByDay[day]:', cur.placesByDay[day])

    const processedPlaces: ItineraryProcessedPlace[] = cur.placesByDay[day].map((place, idx) => {
      console.log(`[getProcessedPlaces] place ${idx}:`, place)
      console.log(`[getProcessedPlaces] place.arrival:`, place.arrival)
      console.log(`[getProcessedPlaces] place.departure:`, place.departure)
      console.log(`[getProcessedPlaces] place.serviceMinutes:`, place.serviceMinutes)
      console.log(`[getProcessedPlaces] place.travelTime:`, place.travelTime)
      console.log(`[getProcessedPlaces] place.waitTime:`, place.waitTime)

      // arrival/departure가 Date 객체거나 문자열일 수 있음
      let arrivalTime = '00:00'
      let departureTime = '00:00'

      if (place.arrival) {
        if (place.arrival instanceof Date) {
          arrivalTime = format(place.arrival, 'HH:mm', { locale: ko })
        } else if (typeof place.arrival === 'string') {
          arrivalTime = place.arrival
        }
      }

      if (place.departure) {
        if (place.departure instanceof Date) {
          departureTime = format(place.departure, 'HH:mm', { locale: ko })
        } else if (typeof place.departure === 'string') {
          departureTime = place.departure
        }
      }

      return {
        order: idx + 1,
        name: place.name,
        category: place.category,
        arrivalTime,
        departureTime,
        serviceMinutes: place.serviceMinutes ?? 0,
        coord: { lng: place.coord.lng, lat: place.coord.lat },
        travelTime: place.travelTime,
        waitTime: place.waitTime,
      }
    })

    console.log('[getProcessedPlaces] processedPlaces:', processedPlaces)
    return { day, places: processedPlaces }
  }

  function printDebug() {
    console.log('🧭 Itinerary Store Debug Info 🧭')
    console.log('User ID:', state.userId)
    console.log('Current Itinerary ID:', state.currentId)
    console.log('Selected Day:', state.selectedDay)
    console.log('Total Itineraries:', Object.keys(state.items).length)

    console.log('\n📌 Current Itinerary:')
    if (current.value) {
      console.log('Places by Day:')
      for (const [day, places] of Object.entries(current.value.placesByDay)) {
        console.log(`  Day ${day}:`)
        places.forEach((p, idx) => {
          console.log(`    ${idx}. ${p.name} (${p.category})`)
        })
      }
    } else {
      console.log('No itinerary selected.')
    }

    console.log('\n🛣 Routing Result:')
    Object.entries(state.routingResult.placesByDay).forEach(([day, places]) => {
      console.log(`  Day ${day}:`)
      places.forEach((p, i) => {
        console.log(`    ${i}. ${p.name} (${p.category})`)
      })
    })
    state.routingResult.path.forEach((dayPaths, day) => {
      if (!dayPaths) {
        console.warn(`⚠️ Path for Day ${day} is undefined`);
        return;
      }
      console.log(`  Path for Day ${day} has ${dayPaths.length} routes`);
    })
  }

  return {
    state,
    current,
    totalPlaces,
    setUserId,
    addItinerary,
    selectItinerary,
    removeItinerary,
    reorderPlaces,
    generateRoutingRequestForSelectedDay,
    updateSelectedDay,
    saveParsedRoutingResult,
    addPlaceToCurrentDay,
    getProcessedPlaces,
    printDebug,
  }
})
