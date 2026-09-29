<template>
  <div class="day-section">
    <div class="day-title center-text">
      <p class="day-subtitle">몇일 일정의 여행을 계획하고 계신가요?</p>
      <h3 class="day-heading">📆 여행 날짜를 선택해주세요</h3>
    </div>

    <div class="day-calendar">
      <Datepicker v-model="selectedRange" mode="range" :range="true" :inline="true" :start-date="today"
        :enable-time-picker="false" :hide-input="true" :auto-apply="true" calendar-only locale="ko"
        format="yyyy-MM-dd" />
    </div>

    <p class="trip-info">
      기간: {{ formattedStart }} → {{ formattedEnd }} (총 {{ tripDays }}일)
    </p>

    <footer class="day-footer flex-between">
      <button class="button-base button-prev" @click="emit('prev')">이전</button>
      <button class="button-base button-next" @click="saveDates">다음</button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/store/user'
import { getTodayDateObject } from '@/utils/date'

const emit = defineEmits<{
  (e: 'next'): void
  (e: 'prev'): void
}>()

const userStore = useUserStore()
const today = getTodayDateObject()

const initialStart = userStore.state.startDate ? new Date(userStore.state.startDate) : today
const initialEnd = userStore.state.endDate ? new Date(userStore.state.endDate) : today

const selectedRange = ref<[Date, Date]>([initialStart, initialEnd])

onMounted(() => {
  selectedRange.value = [initialStart, initialEnd]
  nextTick(() => {
    selectedRange.value = [...selectedRange.value]
  })
})

function formatDate(d: Date) {
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`
}

const formattedStart = computed(() =>
  selectedRange.value[0] ? formatDate(selectedRange.value[0]) : ''
)

const formattedEnd = computed(() =>
  selectedRange.value[0] ? formatDate(selectedRange.value[1]) : ''
)

const tripDays = computed(() => {
  const [start, end] = selectedRange.value
  if (!start || !end) return 0
  const diff = end.getTime() - start.getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24)) + 1
})

function saveDates() {
  const [start, end] = selectedRange.value
  if (!start || !end) {
    alert('시작일과 종료일을 선택해주세요.')
    return
  }

  userStore.setStartDate(start.toISOString().slice(0, 10))
  userStore.setEndDate(end.toISOString().slice(0, 10))
  userStore.setTripDays(tripDays.value)
  emit('next')
}
</script>

<style scoped>
.day-section {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.day-title {
  margin-bottom: 1rem;
}

.day-subtitle {
  font-size: 1rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.day-heading {
  font-size: 1.75rem;
  font-weight: 600;
  color: #0077b6;
}

.day-calendar {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem;
  box-sizing: border-box;
}

.day-calendar :deep(.dp__main) {
  transform: scale(1.1);
  transform-origin: top center;
  width: fit-content;
}

.trip-info {
  text-align: center;
  font-weight: 600;
  font-size: 1.1rem;
  color: #333;
  margin-top: 1rem;
}
</style>
