import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
     resolve: {
       alias: {
         '/webfonts': '/public/webfonts',
       },
     },
  server: {
    proxy: {
      // Proxy /api and /download requests to the Flask backend.
      '/api': {
        target: 'http://10.0.0.35:5000', // Flask dev server
        changeOrigin: true,
      },
      '/download': {
        target: 'http://10.0.0.35:5000', // Flask dev server
        changeOrigin: true,
      },
      '/stream': {
        target: 'http://10.0.0.35:5000',
        changeOrigin: true,
      },
      '/files': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
    host: true,
    strictPort: true,
    port: 5173,
  },
  build: {
    minify: mode === 'production', // Disable minification for dev builds
    sourcemap: mode !== 'production', // Enable source maps for easier debugging
  }
}));