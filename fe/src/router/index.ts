import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'
import StepView from '@/views/StepView.vue'
import MapPage from '@/views/MapView.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'TravelPlannerStep',
        component: StepView,
      },
    ],
  },
  {
    path: '/map',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'DestinationMap',
        component: MapPage,
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
