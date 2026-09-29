<template>
  <div class="popup-row">
    <component
      :is="mainComponent"
      class="popup-panel"
      @close="onClose"
      @get-place-info="onSelectPlace"
    />
    <PlaceDetailCard
      v-if="showDetail && detail"
      :place="detail"
      class="popup-panel"
      @close="onCloseDetail"
      @open-add-place="onAddPlace"
    />
  </div>
</template>

<script setup lang="ts">
import PlaceDetailCard from '@/components/ui/cards/PlaceDetailCard.vue'
import type { PlaceDetail } from '@/types/domain/place'

defineProps<{
  mainComponent: any,
  detail: PlaceDetail | null,
  showDetail: boolean,
  onClose: () => void,
  onCloseDetail: () => void,
  onSelectPlace: (hit: any) => void,
  onAddPlace: () => void,
}>()
</script>

<style scoped>
.popup-row {
  position: absolute;
  top: 0;
  left: calc(100% + 10px);
  display: flex;
  gap: 10px;
  height: 100%;
  z-index: 999;
}
</style>
