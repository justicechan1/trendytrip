// src/composables/useTrendyTripApi.ts

import axios from 'axios'
import type {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios'
import { BACKEND_URL } from '@/utils/constants'
import type { ApiResult } from '@/types/api'

// Axios 인스턴스 생성 (타임아웃 포함)
const api: AxiosInstance = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 100000 // 요청 최대 100초
})

// 요청 전 인터셉터: 토큰 자동 추가 + 개발 모드 디버그 로그
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('authToken')
  if (token && token !== 'null') {
    config.headers = config.headers ?? {}
      ; (config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  if (import.meta.env.DEV) {
    console.debug(
      `[API Request] ${config.method?.toUpperCase()} ${config.url}`,
      config.params ?? config.data
    )
  }
  return config
})

// 응답 후 인터셉터: 공통 에러 로깅 + 개발 모드 디버그 로그
api.interceptors.response.use(
  (response: AxiosResponse) => {
    if (import.meta.env.DEV) {
      console.debug(
        `[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`,
        response.data
      )
    }
    return response
  },
  (error: AxiosError) => {
    console.error(
      `[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}`,
      error.response?.status,
      error.response?.data || error.message
    )
    return Promise.reject(error)
  }
)

export const useTrendyTripApi = () => {
  // 공통 요청 함수
  const request = async <T = any>(
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    options?: { params?: any; data?: any }
  ): Promise<ApiResult<T>> => {
    try {
      const response = await api.request<T>({
        method,
        url,
        params: options?.params,
        data: options?.data
      })
      return { success: true, data: response.data, error: null }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error(`[${method.toUpperCase()} Error] ${url}`, error.response?.data || error.message)
      } else {
        console.error(`[${method.toUpperCase()} Exception] ${url}`, error)
      }
      return { success: false, data: null, error }
    }
  }

  // 메서드 별 래퍼
  const getData = <T = any>(url: string, params?: Record<string, any>) =>
    request<T>('get', url, { params })

  const postData = <T = any>(url: string, data?: any) =>
    request<T>('post', url, { data })

  const putData = <T = any>(url: string, data?: any) =>
    request<T>('put', url, { data })

  const deleteData = <T = any>(url: string, params?: Record<string, any>) =>
    request<T>('delete', url, { params })

  return {
    getData,
    postData,
    putData,
    deleteData
  }
}
