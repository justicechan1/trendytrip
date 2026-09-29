<template>
  <div class="area-section">
    <div class="area-title center-text">
      <p class="area-subtitle">이번 여행, 어디로 떠나볼까요?</p>
      <h3 class="area-heading">가고 싶은 지역을 선택해주세요</h3>
    </div>

    <div class="area-grid">
      <button v-for="area in areas" :key="area" class="area-button" @click="selectArea(area)"
        :class="{ selected: selectedArea === area }">
        {{ area }}
      </button>
    </div>

    <footer class="area-footer flex-end">
      <button class="button-base button-next" @click="emit('next')" :disabled="!userStore.hasArea">
        다음
      </button>
    </footer>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/store/user'
import { areas } from '@/utils/constants'

const emit = defineEmits<{
  (e: 'next'): void
}>()

const userStore = useUserStore()
const selectedArea = computed(() => userStore.state.area)

function selectArea(area: string) {
  userStore.setArea(area)
}
</script>

<style scoped>
.area-section {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  width: 100%;
  height: 100%;
}

.area-title {
  margin-bottom: 2rem;
}

.area-subtitle {
  font-size: 1rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.area-heading {
  font-size: 1.75rem;
  font-weight: 600;
  color: #0077b6;
}

.area-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
  justify-items: center;
}

.area-button {
  width: 100px;
  height: 100px;
  font-size: 1.2rem;
  border: 2px solid #b2ebf2;
  background-color: #f0fbfc;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0.5rem;
}

.area-button:hover {
  background-color: #e0f7fa;
}

.area-button.selected {
  background-color: #00bcd4;
  color: white;
  border-color: #00acc1;
  font-weight: bold;
}
</style>
