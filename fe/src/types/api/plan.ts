import type { Ref } from 'vue'

export interface TripPlanRequest {
  start_transport_id?: number;
  end_transport_id?: number;
  total_days: number;
  start_time: string;
  end_time: string;
  start_date: string;
  hashtags?: string[];
  tripStyle: string;
  daily_locations: number[];
  use_mock?: boolean;
}

export interface Visit {
  order: number;
  place: string;
  arrival_str: string;
  departure_str: string;
  stay_duration: string;
  x_cord: number;
  y_cord: number;
  travel_time?: string;
  wait_time?: string;
}

export interface DayResult {
  day: number;
  visits: Visit[];
  path: number[][][];
}

export interface TripPlanResponse {
  success: boolean;
  error?: string;
  day_results: DayResult[];
}

export interface UsePlanApiReturn {
  planTrip: (request: TripPlanRequest) => Promise<TripPlanResponse>;
  planTripMock: (request: TripPlanRequest) => Promise<TripPlanResponse>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
}