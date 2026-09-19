# Agenda SMMonjos — Setembre 2026

Agenda interactiva *mobile-first* de **Santa Margarida i els Monjos** servida com a web
estàtica a GitHub Pages, preparada per funcionar també com a **Telegram Mini App** sense
canviar el codi.

🌐 https://hrodres.github.io/agenda-smmonjos-mvp/

## Com funciona

És un lloc estàtic **autònom** (no cal compilar):

- `index.html` — app (HTML + JS, icones Lucide inline)
- `styles.css` — estils (inclou els colors de badge de categoria)
- `data/eventos.json` — base de dades dels esdeveniments

S'obre directament al navegador; no cal `npm install` ni `npm run build`.

## Desplegament

GitHub Pages amb **Source: Deploy from a branch → `main`** (arrel). Qualsevol `git push`
a `main` publica el lloc. Abans s'usava la branca `gh-pages`, ja eliminada.

## Dades

`data/eventos.json` és la base de dades. Cada esdeveniment:

`id, titulo, fecha_inicio, fecha_fin, hora_inicio, hora_fin, lugar, categoria, seccio,
precio_socios, precio_general, descripcion, enlace_maps`

**Categories** (badge de color): `Teatre, Música, Infantil, Esport, Formació, Altres,
Cultura, Festes, Gastronomia`. El color del badge s'aplica **inline**
(`style="background:…;color:…"`) per garantir que es veu sempre, independent del CSS extern.

**Seccions** (pestanyes): `Actes, Formació, Esports, Notícies`. Els esdeveniments sense data
apareixen com a "Avís" dins de Notícies.

## Editar dades

Edita `data/eventos.json` i fes `git push`. La extracció inicial es va curar manualment
perquè la sortida automàtica (opencode-go) sortia amb basura en `lugar`/`horario`. Per
regenerar des del PDF oficial hi ha `legacy/scripts/ingest.py` (pipeline obert).

## Telegram Mini App

`index.html` detecta `window.Telegram?.WebApp`: si existeix, crida `ready()`/`expand()` per
integrar-se a pantalla completa; si no, es renderitza com a web estàndard. El mateix codi
serveix per a tots dos destins.

## Històric

El MVP original era en React/Vite (`legacy/`). La versió en producció és aquesta estàtica
autònoma, resultat d'iterar la UI per a mòbil (cercador, botó PDF, vista de calendari per
dies, targeta que obre el detall amb un sol toc, badges de categoria amb color).
