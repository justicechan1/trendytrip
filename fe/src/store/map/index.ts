import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createVNode, render } from 'vue'
import PlaceInfoCard from '@/components/ui/cards/PlaceInfoCard.vue'
import { usePlaceDetail } from '@/composables/usePlaceDetail'
import type { PlaceSummary } from '@/types/api/itinerary.dto'
import { useItineraryStore } from '@/store/itinerary'
import { useRouting } from '@/composables/useRouting'
import type { ItineraryPlace } from '@/types/domain/itinerary'
import type { RoutingRequest } from '@/types/api/routing.dto';

export const useMapStore = defineStore('map', () => {
  const map = ref<naver.maps.Map | null>(null)
  const markers = ref<naver.maps.Marker[]>([])
  const polylines = ref<naver.maps.Polyline[]>([])
  let activeBouncingMarker: naver.maps.Marker | null = null

  // usePlaceDetail 호출
  const { placeDetail, fetchPlaceDetail, isLoading: _isLoading, error: _error } = usePlaceDetail()

  function setMap(newMap: naver.maps.Map) {
    map.value = newMap
  }

  function getMap() {
    return map.value
  }

  function getBounds() {
    return map.value?.getBounds() ?? null
  }

  function panTo(lat: number, lng: number) {
    if (map.value) {
      map.value.panTo(new window.naver.maps.LatLng(lat, lng - 0.005))
    }
  }

  function setZoom(level: number) {
    if (map.value) {
      map.value.setZoom(level)
    }
  }

  function createNumberMarkerIcon(number: number): string {
    number += 1
    const svg = `
      <svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
        <circle cx="20" cy="20" r="18" fill="skyblue" />
        <text x="20" y="26" font-size="18" font-family="Arial" fill="white" font-weight="bold" text-anchor="middle">${number}</text>
      </svg>
    `;
    return 'data:image/svg+xml;base64,' + btoa(svg);
  }

  function addPlaceMarker(place: PlaceSummary, index?: number) {
    if (!map.value) return null;

    const pos = new window.naver.maps.LatLng(place.coord.lat, place.coord.lng);
    let markerIcon;

    if (index === undefined || index === null) {
      markerIcon = {
        url: new URL(`../../assets/${place.category}_icon.png`, import.meta.url).href,
        size: new window.naver.maps.Size(35, 35),
        scaledSize: new window.naver.maps.Size(35, 35),
        origin: new window.naver.maps.Point(0, 0),
        anchor: new window.naver.maps.Point(20, 20)
      };
      const marker = new window.naver.maps.Marker({
        position: pos,
        map: map.value,
        icon: markerIcon,
        name: place.name
      });

      naver.maps.Event.addListener(marker, 'click', async () => {
        console.log(`📍 ${place.name} (${place.category}) 클릭됨`);
        // 이전 마커 애니메이션 제거
        if (activeBouncingMarker && activeBouncingMarker !== marker) {
          activeBouncingMarker.setAnimation(null);
        }
        // 애니메이션 중지 및 바운스 애니메이션 시작
        if (marker.getAnimation() !== null) {
          marker.setAnimation(null);
          activeBouncingMarker = null;
        } else {
          marker.setAnimation(window.naver.maps.Animation.BOUNCE);
          activeBouncingMarker = marker;
        }
        // placeDetail을 가져오기 위한 비동기 호출
        await fetchPlaceDetail({ name: place.name });
        // 팝업을 띄우는 함수 호출
        showPlacePopup(place, marker);
      });
      markers.value.push(marker);
      return marker;
    } else {
      console.log('Marker added:');
      console.log(place.name)
      console.log('Index:', index);
      console.log('Markers:', markers.value);
      console.log('LatLng:', place.coord.lat, place.coord.lng);
      const iconUrl = createNumberMarkerIcon(index);
      markerIcon = {
        url: iconUrl,
        size: new window.naver.maps.Size(40, 40),
        origin: new window.naver.maps.Point(0, 0),
        anchor: new window.naver.maps.Point(20, 20)
      };
      const marker = new window.naver.maps.Marker({
        position: pos,
        map: map.value,
        icon: markerIcon,
        name: place.name
      });
      markers.value.push(marker);
      return marker;
    }
  }

  // 팝업을 띄우는 함수
  function showPlacePopup(_place: PlaceSummary, marker: naver.maps.Marker) {
    // 마커의 LatLng를 가져오기
    const markerPosition = marker.getPosition();
    console.log('Marker LatLng:', markerPosition); // LatLng 값 확인

    // 마커의 화면 내 상대적 위치 계산
    const markerPos = map.value?.getProjection().fromCoordToOffset(markerPosition);
    console.log('Marker Position (screen coordinates):', markerPos); // markerPos 값 확인

    if (!markerPos) return;

    // 팝업 스타일 설정 (위치 및 zIndex)
    const popupStyle = {
      position: 'fixed',
      top: '50%',
      left: 'calc(80%)',
      transform: 'translate(-50%, -50%)',
      zIndex: 9999,
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '10px',
      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
      maxWidth: '300px',
      minWidth: '200px',
    };

    // Vue 컴포넌트로 팝업 띄우기
    const popupComponent = createVNode(PlaceInfoCard, {
      place: placeDetail.value,
      style: popupStyle,
      onClose: () => {
        console.log('팝업 닫기');
        render(null, document.body);
      },
      onOpenAddPlace: () => {
        handleAddPlace();
      },
    });

    console.log("Rendering Popup...");

    render(popupComponent, document.body);
  }

  async function handleAddPlace() {
    const itineraryStore = useItineraryStore();
    const { getParsedRoute } = useRouting();
    if (!placeDetail.value) return;

    const day = itineraryStore.state.selectedDay;
    const backup = [...(itineraryStore.current?.placesByDay[day] ?? [])];

    const newPlace: ItineraryPlace = {
      ...placeDetail.value,
      arrival: '',
      departure: '',
      serviceMinutes: null,
    };

    itineraryStore.addPlaceToCurrentDay(day, newPlace);

    const request: RoutingRequest | null = itineraryStore.generateRoutingRequestForSelectedDay();
    if (!request) {
      itineraryStore.current!.placesByDay[day] = backup;
      return;
    }

    const result = await getParsedRoute(request);
    if (result.success && result.data) {
      itineraryStore.saveParsedRoutingResult(result.data);
    } else {
      itineraryStore.current!.placesByDay[day] = backup;
    }
    console.log('팝업 닫기');
    render(null, document.body);
  }

  function clearMarkers() {
    markers.value.forEach(m => m.setMap(null))
    markers.value = []
  }

  function drawPolyline(
    coords: Array<{ lat: number; lng: number }>,
    options?: {
      strokeColor?: string;
      strokeWeight?: number;
      zIndex?: number;
      segmentIndex?: number; // optional: 디버그나 스타일 구분용
    }
  ) {
    if (!map.value) return null;

    // 필요한 옵션 정의
    const {
      strokeColor = '#007aff',
      strokeWeight = 4,
      zIndex = 1,
    } = options || {};

    // segment 경로 생성
    const path = coords.map(c => new window.naver.maps.LatLng(c.lat, c.lng));

    const line = new window.naver.maps.Polyline({
      path,
      strokeColor,
      strokeWeight,
      zIndex,
      map: map.value,
    });

    polylines.value.push(line);
    return line;
  }

  function clearPolylines() {
    polylines.value.forEach(pl => pl.setMap(null))
    polylines.value = []
  }

  return {
    map,
    markers,
    polylines,
    setMap,
    getMap,
    getBounds,
    panTo,
    setZoom,
    addPlaceMarker,
    clearMarkers,
    drawPolyline,
    clearPolylines
  }
})
