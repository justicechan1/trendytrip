export interface ItineraryPlaceRequest {
  name: string
  arrival_str: string
  departure_str: string
  service_time: number
}

export interface ItineraryRequest {
  places_by_day: {
    [key: string]: ItineraryPlaceRequest[]
  }
}

// 응답 타입 정의
export interface ItineraryPlaceResponse extends ItineraryPlaceRequest {
  address: string
  category: string
  open_time: string
  close_time: string
  convenience: string[]
  description: string
  image_urls: string[]
}

export interface ItineraryResponse {
  places_by_day: {
    [key: string]: ItineraryPlaceResponse[]
  }
}