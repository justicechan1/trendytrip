export const areas = [
  '서울', '경기/인천', '충청', '강원',
  '경상', '전라', '제주', '부산',
  '대구', '광주', '대전', '세종'
]

export const jeju_areas = [
  '애월읍', '성산읍', '조천읍', '한림읍', '제주시', '한경면', '대정읍', '안덕면', '중문', '서귀포시', '남원읍', '표선면', '구좌읍'
]

// 제주 지역명 → 지역 코드 매핑 (백엔드와 동일)
export const JEJU_REGION_CODE_MAP: Record<string, number> = {
  '제주시': 10,
  '애월읍': 101,
  '한림읍': 102,
  '한경면': 103,
  '조천읍': 104,
  '구좌읍': 105,
  '서귀포시': 20,
  '성산읍': 201,
  '표선면': 202,
  '남원읍': 203,
  '안덕면': 204,
  '대정읍': 205,
  '중문': 206,
}

export const BACKEND_URL = 'http://127.0.0.1:8000'

export const CATEGORY_LIST: { label: string; value: string; icon: string }[] = [
  { label: '관광명소', value: 'tourist', icon: 'bi bi-geo-alt' },
  { label: '카페', value: 'cafe', icon: 'bi bi-cup-hot' },
  { label: '음식점', value: 'restaurant', icon: 'bi bi-fork-knife' },
  { label: '숙소', value: 'accommodation', icon: 'bi bi-house' }
]

export type MarkerCategory = 'tourist' | 'cafe' | 'accommodation' | 'restaurant';

export const MarkerIcon: Record<MarkerCategory, string> = {
  tourist: new URL('../assets/tourist_icon.png', import.meta.url).href,
  cafe: new URL('../assets/cafe_icon.png', import.meta.url).href,
  accommodation: new URL('../assets/accommodation_icon.png', import.meta.url).href,
  restaurant: new URL('../assets/restaurant_icon.png', import.meta.url).href,
};

