<template>
  <div class="step-page">
    <main class="step-form">
      <Transition name="fade" mode="out-in">
        <component :is="currentComponent" :key="step" @next="nextPage" @prev="prevPage" />
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

import IntroStep from '@components/steps/IntroStep.vue'
import AreaStep from '@components/steps/AreaStep.vue'
import StyleStep from '@components/steps/StyleStep.vue'
import DayStep from '@components/steps/DayStep.vue'
import TimeStep from '@components/steps/TimeStep.vue'
import "@/styles/inputSection.css"

const step = ref(0)

const steps = [IntroStep, AreaStep, StyleStep, DayStep, TimeStep]

const currentComponent = computed(() => steps[step.value])

function nextPage() {
  if (step.value < steps.length - 1) step.value++
}

function prevPage() {
  if (step.value > 0) step.value--
}
</script>

<style scoped></style>