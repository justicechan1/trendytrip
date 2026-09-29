<template>
  <article class="place-list">
    <p>✅ 추천 장소</p>
    <ul>
      <li v-for="(place, index) in places" :key="index">
        <button class="place-button" @click="handleClick(place)">
          {{ place.name }}
        </button>
      </li>
    </ul>
  </article>
</template>

<script lang="ts" setup>
import { defineProps, defineEmits } from 'vue';
import type { PlaceSearchHit } from '@/types/api/place.dto';

defineProps<{
  places: PlaceSearchHit[];
  keyword: string;
}>();

const emit = defineEmits<{
  (e: 'select', place: PlaceSearchHit): void;
}>();

function handleClick(place: PlaceSearchHit) {
  emit('select', place);
}
</script>

<style scoped>
ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

li {
  margin-bottom: 8px;
}

.place-button {
  width: 100%;
  padding: 10px 16px;
  font-size: 14px;
  text-align: left;
  border: 1px solid #ccc;
  background-color: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.place-button:hover {
  background-color: #f0f8ff;
}
</style>
