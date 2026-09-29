<template>
  <v-timeline align="start" side="end">
    <v-timeline-item
      v-for="(visit, index) in visits"
      :key="index"
      dot-color="blue"
      size="small"
    >
      <div class="d-flex">
        <strong class="me-4">{{ index + 1 }}</strong>

        <div @click="getplaceInfo(visit)" style="cursor: pointer;">
          <strong class="place-name">{{ visit.name }}</strong>
          <span class="category-label">{{ visit.category }}</span>

          <div class="text-caption">
            <div>방문시간: {{ visit.arrivalTime }} ~ {{ visit.departureTime }}</div>
            <div>체류시간: {{ visit.serviceMinutes }} 분</div>
            <div v-if="visit.travelTime">이동시간: {{ visit.travelTime }}</div>
            <div v-if="visit.waitTime">대기시간: {{ visit.waitTime }}</div>
          </div>
        </div>
        <v-btn class="delete-btn ms-auto" variant="text"  @click.stop="deleteVisit(index)">
          <img src="../../assets/delete.png" alt="삭제" class="delete-img" />
        </v-btn>
      </div>
    </v-timeline-item>
  </v-timeline>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import type { PropType } from 'vue'
import type { ItineraryProcessedPlace } from '@/types/api/itinerary.dto'

export default defineComponent({
  name: 'ItineraryTimeline',
  props: {
    visits: {
      type: Array as PropType<ItineraryProcessedPlace[]>,
      required: true
    }
  },
  methods: {
    getplaceInfo(visit: ItineraryProcessedPlace) {
      this.$emit('get-place-info', visit.name)
    },
    deleteVisit(index: number) {
      this.$emit('delete-visit', index)
    }
  }
})
</script>

<style scoped>
.place-name {
  font-size: 16px;
  font-weight: bold;
  color: #3a3a3a;
}

.category-label {
  display: block;
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.text-caption {
  font-size: 12px;
  color: #666;
}

.v-timeline-item {
  background-color: #f9f9f9;
  border-radius: 8px;
  margin: 5px 0;
  padding: 10px;
}

.v-timeline-item .d-flex {
  align-items: center;
}

/* 삭제 이미지 스타일 */
.delete-img {
  width: 80px;
  height: 40px;
}
</style>
