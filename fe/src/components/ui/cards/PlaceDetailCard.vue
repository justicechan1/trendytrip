<template>
  <div class="place-detail-card" v-if="place">
    <header class="popup-header">
      <div class="left-section">
        <a :href="'https://www.instagram.com/explore/search/keyword/?q=' + encodeURIComponent(place.name)"
          target="_blank" class="instagram_link">
          <img src="@/assets/instagram.png" alt="Instagram" class="instagram_img" />
        </a>
        <h2>{{ place.name }}</h2>
      </div>
      <span class="category">{{ place.category }}</span>
    </header>

    <p class="address">{{ place.address }}</p>
    <p class="running-time">영업시간: {{ formatTime(place.openTime) }} ~ {{ formatTime(place.closeTime) }}</p>
    <p class="convenience" style="color: gray">{{ place.conveniences.join(', ') }}</p>

    <article class="image-slider" v-if="place.images.length">
      <div class="masonry-wrapper">
        <div class="masonry-feed">
          <img v-for="(image, index) in place.images" :key="index" :src="image" :alt="`Image ${index + 1}`"
            class="masonry-img" />
        </div>
      </div>
    </article>

    <footer>
      <button class="button-add" @click="emit('open-add-place')">추가➕</button>
      <button class="button-close" @click="emit('close')">닫기❌</button>
    </footer>
  </div>

  <div v-else>
    <p>장소 정보가 없습니다.</p>
  </div>
</template>

<script lang="ts" setup>
import { defineProps, defineEmits } from 'vue'
import type { PlaceDetail } from '@/types/domain/place'

defineProps<{ place: PlaceDetail | null }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'open-add-place'): void
}>()

function formatTime(time: string): string {
  const [hourStr, minuteStr] = time.split(':')
  const hour = parseInt(hourStr)
  const minute = parseInt(minuteStr)
  const period = hour < 12 ? '오전' : '오후'
  const formattedHour = hour % 12 === 0 ? 12 : hour % 12
  return `${period} ${formattedHour}시${minute !== 0 ? ` ${minute}분` : ''}`
}
</script>

<style scoped>
.place-detail-card {
  position: absolute;
  top: 0;
  left: calc(100% + 10px);
  width: 22vw;
  height: 100%;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
  font-family: 'Noto Sans KR', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.instagram_link {
  display: inline-block;
  cursor: pointer;
}

.instagram_img {
  width: 40px;
  height: 40px;
}

h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
}


.category {
  background-color: skyblue;
  color: white;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.9rem;
  align-self: flex-start;
}

.address,
.running-time {
  font-size: 1rem;
  margin: 0;
}

section {
  margin-bottom: 10px;
}

.convenience-info p {
  font-size: 0.95rem;
  margin-top: 8px;
}

.image-slider {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  overflow-y: auto;
  height: 100%;
  width: 100%;
}

.masonry-wrapper {
  display: flex;
  justify-content: center;
}

.masonry-feed {
  column-count: 2;
  column-gap: 8px;
}

.masonry-img {
  width: 100%;
  margin-bottom: 8px;
  border-radius: 8px;
  display: block;
  break-inside: avoid;
  object-fit: cover;
}

footer {
  margin-top: auto;
  display: flex;
  gap: 12px;
  justify-items: auto;
}

.button {
  flex: 1;
  padding: 10px 0;
  font-size: 0.95rem;
  font-weight: 600;
  background-color: #fbe9e7;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

button.button-close {
  color: #c62828;
}

button.button-add {
  color: #2e7d32;
}

button.button-add:hover {
  background-color: #c8e6c9;
}

.button-close:hover {
  background-color: #ffcdd2;
}
</style>
