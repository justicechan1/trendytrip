// src/main.ts
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import { pinia } from '@/store'

import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

import Datepicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

import Vue3Toastify from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'

// 1. Vuetify 세팅
const vuetify = createVuetify({
  components,
  directives,
})

// 2. 앱 생성
const app = createApp(App)

// 3. 플러그인 등록 순서 중요
app.use(router)
app.use(pinia)
app.use(vuetify)
app.use(Vue3Toastify, {
  autoClose: 3000,
  theme: 'auto', 
})

// 4. 글로벌 컴포넌트 등록
app.component('Datepicker', Datepicker)

// 5. 마운트
app.mount('#app')
