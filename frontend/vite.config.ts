import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ai-sdc-profiling',
  server: {
    host: '0.0.0.0',
    port: 5175,
    allowedHosts: ['failsafe.amd.com', 'localhost', '.amd.com'],
    proxy: {
      '/ai-sdc-profiling-api': {
        target: process.env.VITE_API_URL || 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/ai-sdc-profiling-api/, ''),
      },
    },
  },
})
