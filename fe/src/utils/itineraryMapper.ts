import type { ItineraryProcessedPlace } from '@/types/api/itinerary.dto'
import type { ItineraryRequest, ItineraryPlaceRequest } from '@/types/api/trip'

export function buildItineraryRequest(
  visitsByDay: Record<string, ItineraryProcessedPlace[]>
): ItineraryRequest {
  const places_by_day: Record<string, ItineraryPlaceRequest[]> = {}

  for (const [day, visits] of Object.entries(visitsByDay)) {
    places_by_day[day] = visits.map(v => ({
      name: v.name,
      arrival_str: v.arrivalTime,
      departure_str: v.departureTime,
      service_time: v.serviceMinutes
    }))
  }

  return { places_by_day }
}