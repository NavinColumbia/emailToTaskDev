import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/auth': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/tasks': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/calendar-events': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/fetch-emails': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/user': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/logout': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/authorize': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
      '/oauth2callback': {
        target: process.env.VITE_BASE_URL || 'http://localhost:5001',
        changeOrigin: true,
        cookieDomainRewrite: '',
      },
    },
  },
})
