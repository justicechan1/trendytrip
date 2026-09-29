// src/types/domain/place.ts
import type { Category, Coordinates2D, ISOTime, ISODate, PlaceName } from '../common';

export interface PlaceMarker {
  name: PlaceName;
  category: Category;
  coord: Coordinates2D;
}

export interface PlaceDetail extends PlaceMarker {
  address: string;
  openTime: ISOTime;
  closeTime: ISOTime;
  conveniences: string[];
  description: string;
  images: string[];
}

export interface PlaceInfo {  // 일정 저장 컴포넌트에 사용될 인터페이스
  name: PlaceName;
  area: string;
  startDate: ISODate;
  endDate: ISODate;
  tripDays: number;
  category: Category;
  address: string;
  openTime: ISOTime;
  closeTime: ISOTime;
  conveniences: string[];
  description: string;
  images: string[];
  serviceMinutes: number; // 체류 시간
  arrivalTime: string;
  departureTime: string;
}