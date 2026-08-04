import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig(() => ({
  plugins: [
    react(),
    // Generates stats.html in dist/ after every build — open it to inspect bundle sizes.
    // Only runs during build, not dev server.
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],

  resolve: {
    alias: {
      // Every internal import uses this: '@/components/ui/Button'.
      // Relative paths deeper than './' are not used anywhere in src/.
      '@': path.resolve(__dirname, 'src'),
    },
  },

  server: {
    // Forwards every /api/* call to the backend so the browser sees it as
    // same-origin — matches services/httpClient.js, which stays on relative
    // URLs in dev for exactly this reason. No CORS setup needed locally;
    // the backend's CORS config only has to cover real deployed origins.
    // Hardcoded to match httpClient.js's own fallback and realify-mc's actual
    // default (config.py: REALIFY_PORT defaults to 8001, not 8000).
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },

  build: {
    // Warn when any chunk exceeds 500 kB (Vite default is 500, made explicit)
    chunkSizeWarningLimit: 500,

    rollupOptions: {
      output: {
        // Split heavy vendor libraries into separate cacheable chunks.
        // These only re-download when their version changes, not on every app deploy.
        manualChunks(id) {
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3-') || id.includes('node_modules/victory-vendor')) {
            return 'vendor-recharts';
          }
          if (id.includes('node_modules/framer-motion')) {
            return 'vendor-motion';
          }
          if (id.includes('node_modules/react-router') || id.includes('node_modules/@remix-run')) {
            return 'vendor-router';
          }
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom') || id.includes('node_modules/scheduler')) {
            return 'vendor-react';
          }
          if (id.includes('node_modules/zustand')) {
            return 'vendor-zustand';
          }
          if (id.includes('node_modules/axios')) {
            return 'vendor-axios';
          }
        },
      },
    },
  },
}))
