import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' -> rutas relativas, compatibles directamente con GitHub Pages
export default defineConfig({
  base: './',
  plugins: [react()],
})
