import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === 'production' ? '/static/workflow/' : '/',
  build: {
    outDir: '../static/workflow',
    emptyOutDir: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    pool: 'threads',
    minWorkers: 1,
    maxWorkers: 1,
  },
})
