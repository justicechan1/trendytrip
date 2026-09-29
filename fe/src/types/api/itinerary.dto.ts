import type { DayList, ISODate, ISOTime, Category, PlaceName, Id, Coordinates2D } from '../common';
import type { UserPreferences } from '../domain/user';

export interface ItineraryPlaceInput { name: PlaceName; }

export interface ItineraryPostBody {
  date:{
    userId: Id;
    startDate: ISODate;
    endDate: ISODate;
    arrivalTime: ISOTime;
    departureTime: ISOTime;
    startPlace: string;
    endPlace: string;
  }
  user: UserPreferences;
  placesByDay: DayList<ItineraryPlaceInput>;
  dailyLocations?: number[];  // 일별 지역 코드 배열 (optional)
}

export interface PlaceSummary {
  name: PlaceName;
  coord: { lng: number; lat: number };
  category: Category;
  arrival?: ISOTime;
  departure?: ISOTime;
}

export interface ItineraryResponse {
  placesByDay: DayList<PlaceSummary>;
}

export interface ItineraryProcessedPlace {
  order: number
  name: string
  category: string
  arrivalTime: string
  departureTime: string
  serviceMinutes: number
  coord: Coordinates2D
}
