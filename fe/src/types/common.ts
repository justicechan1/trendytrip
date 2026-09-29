// src/types/common.ts
/** 기본 ID 타입 */
export type Id = string;

// /** YYYY-MM-DD 형식 */
// export type ISODate = `${number}-${number}-${number}` | null;

// /** HH:mm 형식 */
// export type ISOTime = `${number}:${number}` | null;

/** YYYY-MM-DD 형식 */
export type ISODate = string;

/** HH:mm 형식 */
export type ISOTime = string;

/** 좌표 */
export interface Coordinates2D {
  lng: number; // 경도(lng)
  lat: number; // 위도(lat)
}

/** 지도 뷰포트 */
export interface Viewport {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/** 날짜(인덱스)별 리스트 */
export type DayList<T> = Record<number, T[]>;

/** 카테고리 리터럴 */
export const CATEGORIES = [
  'tourist',
  'cafe',
  'restaurant',
  'accommodation',
  'transport'
] as const;
export type Category = string;

/** 해시태그 */
export interface Hashtag {
  name: string;
}

export interface Icon {
  label: string
  value: string
  icon: string
}

export type PlaceName = string;
