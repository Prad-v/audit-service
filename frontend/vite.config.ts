import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    hmr: {
      overlay: true
    },
    proxy: {
      '/api/v1/alerts': {
        target: 'http://alerting:8001',
        changeOrigin: true,
      },
      '/events/api/v1': {
        target: 'http://api-gateway:8002',
        changeOrigin: true,
      },
      '/api/v1/cloud': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/audit': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/llm': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/mcp': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/metrics': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/auth': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/health': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/api/v1/outages': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/incidents': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/processors': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/subscriptions': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/events': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/pubsub': {
        target: 'http://events:8003',
        changeOrigin: true,
      },
      '/api/v1/webhook': {
        target: 'http://host.docker.internal:8003',
        changeOrigin: true,
      },
      '/api/v1/integrations': {
        target: 'http://audit-service:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
