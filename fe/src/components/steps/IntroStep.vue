<template>
  <div class="intro-content flex-column center-text">
    <h2 class="intro-subtitle">사용자 맞춤 감성 여행 플랜 웹사이트</h2>
    <h1 class="intro-title">Trendy Trip ✈️</h1>
    <p class="intro-description">시작하려면 버튼을 눌러주세요</p>
    <button class="button-base button-next intro-button" @click="emit('next')">
      시작하기
    </button>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  (e: 'next'): void
}>()
</script>

<style scoped>
.intro-content {
  justify-content: center;
  align-items: center;
  flex: 1;
  width: 100%;
}

.intro-subtitle {
  font-size: 1.25rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.intro-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: skyblue;
  margin-bottom: 1rem;
}

.intro-description {
  font-size: 1rem;
  color: #444;
  margin-bottom: 2rem;
}

.intro-button {
  padding: 0.75rem 2rem;
  font-size: 1.1rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.intro-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 188, 212, 0.4);
}
</style>
