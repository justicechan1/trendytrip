// src/shims-vue-datepicker.d.ts
import { DefineComponent } from 'vue'

declare module '@vuepic/vue-datepicker' {
  const Datepicker: DefineComponent<{}, {}, any>
  export default Datepicker
}
