import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    host: true,
    strictPort: false,
    proxy: {
      '/screenshot': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/shorten': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '^/s/[^/]+$': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/cache': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  base: '/',
  optimizeDeps: {
    include: ['react', 'react-dom'],
  },
})