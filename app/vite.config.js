import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The app is fully static: it reads /data/dashboard.json (pre-built by
// scripts/build_dashboard_data.py) and runs entirely client-side.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: 'dist',
  },
})
