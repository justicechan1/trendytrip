import { ref, onMounted } from 'vue'
import type { Ref } from 'vue'

interface NaverMapOptions {
  maxRetries?: number  // 스크립트 로드 최대 재시도 횟수
  retryDelay?: number  // 재시도 간 딜레이(ms)
  timeout?: number     // SDK 로드 대기 타임아웃(ms)
  zoom?: number        // 초기 줌 레벨
}

export function useNaverMap(
  centerLat: number = 33.4,
  centerLng: number = 126.55,
  options: NaverMapOptions = {}
): { map: Ref<naver.maps.Map | null> } {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    timeout = 5000,
    zoom = 13,
  } = options

  const map = ref<naver.maps.Map | null>(null)

  function loadScript(retriesLeft: number, delay: number): Promise<void> {
    console.log('로드 스크립트 시작', retriesLeft, delay)
    return new Promise((resolve, reject) => {
      const existing = document.getElementById('naver-map-script') as HTMLScriptElement | null
      if (existing) {
        if (window.naver?.maps) {
          console.log('이미 스크립트가 로드되었습니다.')
          resolve()
        } else {
          existing.addEventListener('load', () => resolve(), { once: true })
          existing.addEventListener(
            'error',
            () => {
              document.head.removeChild(existing)
              if (retriesLeft > 0) {
                setTimeout(
                  () => loadScript(retriesLeft - 1, delay * 2).then(resolve).catch(reject),
                  delay
                )
              } else {
                reject(new Error('네이버 지도 스크립트 로드 실패'))
              }
            },
            { once: true }
          )
        }
        return
      }

      const script = document.createElement('script')
      script.id = 'naver-map-script'
      script.src =
        `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=i413nee7uu`
      script.async = true
      script.defer = true
      script.onload = () => {
        console.log('네이버 지도 스크립트 로드 완료')
        resolve()
      }
      script.onerror = () => {
        document.head.removeChild(script)
        if (retriesLeft > 0) {
          setTimeout(
            () => loadScript(retriesLeft - 1, delay * 2).then(resolve).catch(reject),
            delay
          )
        } else {
          reject(new Error('네이버 지도 스크립트 로드 실패'))
        }
      }
      document.head.appendChild(script)
    })
  }

  function waitForNaverMaps(timeoutMs: number): Promise<void> {
    console.log('네이버 지도 SDK 대기 시작')
    return new Promise((resolve, reject) => {
      const interval = 100
      let elapsed = 0
      const timer = setInterval(() => {
        if (window.naver?.maps) {
          clearInterval(timer)
          console.log('네이버 지도 SDK 로드 완료')
          resolve()
        } else if ((elapsed += interval) >= timeoutMs) {
          clearInterval(timer)
          reject(new Error('네이버 지도 SDK 로드 타임아웃'))
        }
      }, interval)
    })
  }

  onMounted(async () => {
    const el = document.getElementById('map')
    if (!el) {
      console.warn('❌ [useNaverMap] #map element not found')
      return
    }

    try {
      console.log('지도 초기화 시작')
      await loadScript(maxRetries, retryDelay)
      await waitForNaverMaps(timeout)

      map.value = new window.naver.maps.Map(el, {
        center: new window.naver.maps.LatLng(centerLat, centerLng),
        zoom,
      })
      console.log('✅ [useNaverMap] 지도 초기화 완료', centerLat, centerLng)
    } catch (err) {
      console.error('❌ [useNaverMap]', err)
    }
  })

  return { map }
}
