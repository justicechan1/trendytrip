import type { PlaceSummary } from '@/types/api/itinerary.dto';
import type { ItineraryPlace } from '@/types/domain/itinerary';

export function convertPlaceSummaryToItineraryPlace(summary: PlaceSummary): ItineraryPlace {
  console.log('[converters] summary.arrival:', summary.arrival, typeof summary.arrival)
  console.log('[converters] summary.departure:', summary.departure, typeof summary.departure)

  return {
    name: summary.name,
    category: summary.category,
    coord: {
      lat: summary.coord.lat,
      lng: summary.coord.lng,
    },
    description: '',
    address: '',
    openTime: '',
    closeTime: '',
    conveniences: [],
    images: [],
    arrival: summary.arrival || '',
    departure: summary.departure || '',
    serviceMinutes: summary.serviceMinutes ?? 0,
    travelTime: summary.travelTime,
    waitTime: summary.waitTime,
  };
}
