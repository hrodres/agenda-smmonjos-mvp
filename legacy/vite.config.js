import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' -> rutas relativas, compatibles directamente amb GitHub Pages
// Noms d'asset ESTABLES (sense hash ni timestamp): així qualsevol index.html
// cachejat pel navegador sempre troba el seu asset (evita pantalla en blanc
// per HTML que apunta a un hash ja esborrat per un force-push previ).
// El plugin treu 'crossorigin' del <script type=module> per evitar fallades
// silencioses en mobil (Pages + module + crossorigin pot no executar-se).
export default defineConfig({
  base: './',
  plugins: [
    react(),
    {
      name: 'strip-crossorigin',
      transformIndexHtml(html) {
        return html.replace(/<script([^>]*)\s+crossorigin([^>]*)>/g, '<script$1$2>')
      },
    },
  ],
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/index.js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name][ext]`,
      },
    },
  },
})
