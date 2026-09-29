import axios from 'axios'
import type { Hashtag } from '@/types/common'

// 지역별 해시태그 조회
export async function fetchHashtags(area: string): Promise<Hashtag[]> {
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/users/maps/local_hashtag', {
      local_name: area
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    if (!response.data || !Array.isArray(response.data.tag)) {
      console.warn(`${area} 해시태그 데이터가 배열이 아님`, response.data)
      return []
    }

    console.log(`[fetchHashtags] ${area} 서버 응답(raw):`, response.data.tag)

    // tag.hashtag 값만 뽑아서 Hashtag[] 형태로 반환
    const hashtags: Hashtag[] = response.data.tag.map((item: { hashtag: string }) => ({
      name: item.hashtag
    }))

    console.log(`[fetchHashtags] ${area} 해시태그 리스트:`, hashtags)
    return hashtags
  } catch (error) {
    console.error(`${area} 해시태그 불러오기 실패:`, error)
    return []
  }
}