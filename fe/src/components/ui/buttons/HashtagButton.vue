<template>
  <div>
    <div class="button-container">
      <button v-for="(tag, index) in hashtags" :key="index"
        :class="['hashtag-button', { 'selected': selectedHashtag === tag.name }]" @click="handleClick(tag)">
        {{ tag.name }}
      </button>
    </div>

    <!-- 선택된 해시태그 표시 -->
    <div v-if="selectedHashtag" class="selected-hashtag">
      <p>선택된 해시태그: {{ selectedHashtag }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HashtagButtons',
  props: {
    selectedHashtag: {
      type: String,
      default: null
    },
    hashtags: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    handleClick(tag) {
      const newSelected = this.selectedHashtag === tag.name ? null : tag.name
      this.$emit("select-hashtag", newSelected)
    }
  }
}
</script>

<style scoped>
.button-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  justify-content: flex-end;
}

.hashtag-button {
  background-color: white;
  color: skyblue;
  border: 2px solid skyblue;
  border-radius: 15px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.hashtag-button:hover {
  background-color: deepskyblue;
  color: white;
}

/* 선택된 상태일 때 스타일 */
.hashtag-button.selected {
  background-color: deepskyblue;
  color: white;
  border-color: deepskyblue;
}

.selected-hashtag {
  margin-top: 20px;
  font-size: 18px;
  color: deepskyblue;
}
</style>
