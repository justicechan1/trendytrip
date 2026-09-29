// src/stores/utils/createEntityStore.ts
import { defineStore } from 'pinia'

export function createEntityStore<T>(storeId: string) {
  return defineStore(storeId, {
    state: () => ({
      items: {} as Record<string, T>,
    }),
    getters: {
      getById: (state) => (id: string): T | null => state.items[id] ?? null,
      getAll: (state): T[] => Object.values(state.items),
    },
    actions: {
      add(id: string, entity: T) {
        this.items = { ...this.items, [id]: entity }
      },
      remove(id: string) {
        const { [id]: _, ...rest } = this.items
        this.items = rest
      },
    },
  })
}
