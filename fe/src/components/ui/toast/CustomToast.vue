<template>
  <div>
    <p>{{ message }}</p>
    <button @click="handleClick" style="margin-top: 10px; color: #007bff; background: none; border: none; cursor: pointer;">
      {{ actionText }}
    </button>
  </div>
</template>

<script setup lang="ts">

const { message, actionText, onAction } = defineProps<{
  message: string
  actionText: string
  onAction: () => void
}>()

function handleClick() {
  onAction()
}

</script>
