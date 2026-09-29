<template>
    <div id="category_btn">
        <button v-for="category in categoryList" :key="category.value"
            :class="['category-button', { selected: selectedCategory === category.value }]"
            @click="$emit('select-category', category.value)">
            <i :class="category.icon" class="bi-icon"></i>
            <span>{{ category.label }}</span>
        </button>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import type { PropType } from 'vue'

import { CATEGORY_LIST } from '@/utils/constants';  
import 'bootstrap-icons/font/bootstrap-icons.css';

export default defineComponent({
    name: 'CategoryButton',
    props: {
        selectedCategory: {
            type: String as PropType<string | null>,
            required: false,
            default: null,
        }
    },
    setup() {
        return {
            categoryList: CATEGORY_LIST
        }
    },
    emits: ['select-category']
})
</script>

<style>
#category_btn {
    top: 4%;
    right: 2%;
    display: flex;
    gap: 10px;
    position: absolute;
    z-index: 10;
}

.category-button {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 2px solid white;
    background: rgba(73, 210, 255, 0.5);
    flex-direction: column;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    cursor: pointer;
}

.category-button:hover {
    background: deepskyblue;
}

.category_btn.selected {
    background-color: deepskyblue;
    border-color: white;
}

.bi-icon {
    font-size: 28px;
    margin-bottom: 0;
}
</style>