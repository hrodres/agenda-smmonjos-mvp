# Agenda SMMonjos — MVP

Prototipo interactivo de la **agenda cultural de Santa Margarida i els Monjos** (setembre 2026).
App web móvil (React + Vite + Tailwind) alojada en GitHub Pages, preparada para convertirse en
**Telegram Mini App** sin modificar el código.

- 🌐 Demo: `https://<tu-usuario>.github.io/agenda-smmonjos-mvp/`
- 📄 Datos en vivo extraídos del PDF oficial del Ajuntament.

---

## Estructura

```
agenda-smmonjos-mvp/
├── .github/workflows/deploy.yml   # CI: push a main → build → gh-pages
├── scripts/ingest.py              # Pipeline de ingesta (PDF → opencode-go → JSON)
├── public/data/eventos.json       # Base de datos estática (generada por el pipeline)
├── src/                           # App React (mobile-first, Lucide Icons)
├── index.html
├── vite.config.js                 # base: './' para GitHub Pages
├── tailwind.config.js
└── package.json
```

## Pipeline de ingesta (`scripts/ingest.py`)

1. Descarga el PDF oficial de la agenda.
2. Extrae el texto por páginas con `pdfplumber`.
3. Llama a la API de **opencode-go** aplicando *Best Model Selection*: prueba los modelos más
   potentes/precisos en orden hasta obtener una respuesta válida, y fuerza un **JSON Schema
   estricto** con los eventos (titulo, fechas, hora, lugar, categoria, precios, descripcion, Maps).
4. Guarda el resultado en `public/data/eventos.json`.

### Modelo seleccionado (Best Model Selection)
El pipeline usa el primer modelo disponible de este ranking (configurable con `OPENCODE_MODEL`):

| Orden | Modelo opencode-go                         | Uso                                       |
|------:|--------------------------------------------|-------------------------------------------|
| 1     | `opencode-go/gpt-5-6-luna`                 | extracción principal (top precisión)      |
| 2     | `opencode-go/deepseek-v4-pro`             | fallback de capacidad                     |
| 3     | `opencode-go/hy3`                         | fallback final                            |

Si `OPENCODE_API_KEY` no está definida (o todos los modelos fallan), el pipeline **no rompe**:
escribe un *seed* embebido (extracción curada del PDF oficial) para que el MVP siempre tenga datos.

```bash
pip install pdfplumber requests
export OPENCODE_API_KEY="tu-clave"          # opcional
python scripts/ingest.py                    # regenera public/data/eventos.json
python scripts/ingest.py --force-seed       # escribe solo el seed
```

## Desarrollo local (web)

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # genera dist/ (lista para Pages)
```

## Despliegue en GitHub Pages

El workflow `.github/workflows/deploy.yml` compila y publica en la rama `gh-pages` con cada
`git push` a `main`. Activa Pages en el repo → *Build and deployment* → **Source: GitHub Actions**.

## Detección nativa de Telegram Mini App

En `src/App.jsx` un `useEffect` detecta `window.Telegram?.WebApp`: si existe, ejecuta `ready()`
y `expand()` para integrarse como Mini App a pantalla completa; si no, se renderiza como web
estándar. Mismo código para ambos destinos.

## Categorías

`Teatro · Música · Infantil · Deportes · Formación · Otros` (badges de color en las tarjetas).

## Banner B2B

Espacio destacado de patrocinio ("¿Dónde cenar este fin de semana?") listo para comercializar.
