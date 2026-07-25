import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.VITE_FRONTEND_PORT || '3000', 10),
    proxy: {
      '/auth': {
        target: process.env.VITE_AUTH_API_URL || 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api': {
        target: process.env.VITE_BACKEND_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});