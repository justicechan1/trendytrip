import axios from "axios"
import { BACKEND_URL } from '@/utils/constants'

// 요청 타입 정의
import type { ItineraryRequest, ItineraryResponse } from '@/types/api/trip'

// 일정 저장 API
export async function saveItinerary(
  payload: ItineraryRequest
): Promise<ItineraryResponse | null> {
  try {
    const response = await axios.post<ItineraryResponse>(
      `${BACKEND_URL}/api/users/schedules/itinerary`,
      payload,
      {
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
      }
    )

    console.log("[saveItinerary] 서버 응답(raw):", response.data)
    return response.data
  } catch (error) {
    console.error("[saveItinerary] 일정 저장 실패:", error)
    return null
  }
}