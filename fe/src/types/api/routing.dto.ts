import type { DayList, ISOTime, Coordinates2D, PlaceName, Id, Category } from '../common';
import type { PlaceMarker } from '../domain/place';

export interface RoutingRequestPlaceInput {
  name: PlaceName;
  serviceMinutes: number | null;
}

export interface RoutingRequest {
  userId: Id;
  placesByDay: DayList<RoutingRequestPlaceInput>;
}

export interface RoutingPlace extends PlaceMarker {
  address: string;
  arrival: ISOTime;
  departure: ISOTime;
  serviceMinutes: number | null;
}

export interface RoutingResponse {
  placesByDay: DayList<RoutingPlace>;
  path: Coordinates2D[][];
}

// 입력 타입 정의 (요청 전에 준비되는 로우 데이터)
export interface RawPlaceInput {
  name: string;
  serviceMinutes?: number | null;
  coord?: Coordinates2D;
  category?: string;
  openTime?: string;
  closeTime?: string;
}

export interface RawInputData {
  userId: string;
  placesByDay: Record<string, RawPlaceInput[]>;
}

export interface ParsedRoute {
  day: string;
  places: {
    name: string;
    address: string;
    arrival: string;
    departure: string;
    serviceMinutes: number | null;
    category: Category;
    coord:{
      lat: number;
      lng: number;
    }
  }[];
  path: Coordinates2D[][];
}