// src/stores/index.ts
import { createPinia } from 'pinia'

export const pinia = createPinia()

// 여기서 각 스토어를 export도 가능
export * from './user'
export * from './map'
export * from './itinerary'
