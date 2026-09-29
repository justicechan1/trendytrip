// src/types/domain/itinerary.ts
import type { DayList, ISOTime } from '../common';
import type { PlaceDetail } from './place';

export interface ItineraryPlace extends PlaceDetail {
  arrival: ISOTime;
  departure: ISOTime;
  serviceMinutes: number | null;
}

export interface InternalItinerary {
  placesByDay: DayList<ItineraryPlace>;
}