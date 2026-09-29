<template>
  <div class="popup-container">
    <header>
      <h2>📜 최종 여행 플래너</h2>
    </header>

    <article class="save-list">
      <!-- 저장 버튼 클릭 시 SaveSchedule 열림 -->
      <button class="button-save" @click="showSaveSchedule = true">
        여행 플래너 확인하기✅
      </button>

      <h3 style="margin: 5px;"> 위의 버튼을 누르시면, 선택하신 장소에 대한 상세 여행 플래너를 확인할 수 있어요!</h3>
    </article>

    <footer>
      <button class="button-close" @click="emit('close')">닫기❌</button>
    </footer>

    <!-- SaveSchedule 컴포넌트 -->
    <teleport to="body">
      <SaveSchedule
        v-if="showSaveSchedule"
        @close="showSaveSchedule = false"
        class="side-schedule"
      />
    </teleport>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import SaveSchedule from '@/components/popup/SaveSchedule.vue'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const showSaveSchedule = ref(false)   // ✅ ref로 선언
</script>

<style scoped>
@import "@/styles/popup.css";

.button-save {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
}

.side-schedule {
  position: fixed;
  top: 50%;
  left: 60%;
  transform: translate(-50%, -50%); /* 화면 가운데 정렬 */
  z-index: 9999;

  /* 반응형 크기 */
  width: min(180vw, 240vw);
  max-height: 90vh;
  overflow-y: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  padding: 1rem;
}
</style>
