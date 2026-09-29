import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@styles': path.resolve(__dirname, './src/styles'),
      '@composables': path.resolve(__dirname, './src/composables'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types'),
      '@views': path.resolve(__dirname, './src/views'),
      '@components': path.resolve(__dirname, './src/components'),
      '@utils': path.resolve(__dirname, './src/utils'),
    }
  },
  server: {
    cors: true,
    proxy: {
      '/nrbe.map.naver.net': {
        target: 'https://nrbe.map.naver.net',
        changeOrigin: true,  // 요청 헤더의 origin을 target 서버의 origin으로 변경
        secure: false,       // https에 대한 인증서 검증을 비활성화
        rewrite: (path) => path.replace(/^\/nrbe.map.naver.net/, ''),  // 요청 경로에서 앞부분을 제거
      },
    },
  },
})
