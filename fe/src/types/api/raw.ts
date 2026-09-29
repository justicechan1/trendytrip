import type { Hashtag, Category } from '@/types/common'

export interface RawPlaceDetailRequest {
  name: string;
}

export interface RawPlaceDetailResponse {
  places: {
    name: string;
    address: string;
    x_cord: number;
    y_cord: number;
    category: string;
    description?: string;  // 백엔드에서 제공하지 않을 수 있음
    open_time: string;
    close_time: string;
    convenience: string;
    image_urls: string[];
  };
}

export interface RawCategoryToHashtagRequest {
  category: string;
  viewport: {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
  };
}

export interface RawCategoryToHashtagResponse {
  tag: {
    hashtag: string;
  }[];
}

export interface RawHashtagToPlaceRequest {
  category: string;
  tag: {
    hashtag: Hashtag;
  }[];
  viewport: {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
  };
}

export interface RawHashtagToPlaceResponse {
  select_hashtage: {
    name: string;
    category: Category;
    x_cord: number;
    y_cord: number;
    similarity: number;
  }[];
}

export type RawPlace = {
  name: string;
  x_cord: number;
  y_cord: number;
  category: string;
};

// Init API 응답의 visit 구조
export interface RawVisit {
  order: number;
  place: string;
  arrival_str: string;
  departure_str: string;
  stay_duration: string;
  travel_time: number;
  wait_time: number;
  x_cord: number;
  y_cord: number;
  category: string;
}

// Init API 응답의 day_schedule 구조
export interface RawDaySchedule {
  day: number;
  date: string;
  visits: RawVisit[];
  path: number[][][];
}

// Init API 응답 구조
export interface RawInitResponse {
  success: boolean;
  error?: string;
  total_days: number;
  start_date: string;
  end_date: string;
  day_schedules: RawDaySchedule[];
}

// 기존 호환성을 위해 유지 (Routing API용)
export type RawItinerary = {
  places_by_day: Record<string, RawPlace[]>;
};

export interface RawPlaceSearchRequest {
  name: string;
}

export interface RawPlaceSearchResponse {
  search: {
    name: string;
  }[];
}

export interface RawRoutingRequestDto {
  user_id: string;
  places_by_day: Record<
    string,
    {
      name: string;
      service_time: number;
    }[]
  >;
}

export interface RawRoutingResponseDto {
  places_by_day: Record<
    string,
    {
      name: string;
      address: string;
      arrival_str: string;
      departure_str: string;
      service_time: string;
      x_cord: number;
      y_cord: number;
      category: Category;
    }[]
  >;
  path: [number, number][][]; 
}