import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // For GitHub Pages, use repository name as base path
  // For other deployments (Vercel, Netlify), this will be '/'
  base: process.env.GITHUB_PAGES === 'true' ? '/Uber_reserve_supply_forecaster/' : '/',
})
