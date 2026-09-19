# Agenda SMMonjos — web estàtica multi-mes

Agenda interactiva *mobile-first* de **Santa Margarida i els Monjos**, servida com a web
estàtica a GitHub Pages. Suporta **diversos mesos** (una agenda per mes, seleccionable
des del propi lloc) i està preparada per funcionar també com a **Telegram Mini App** sense
canviar el codi.

🌐 https://hrodres.github.io/agenda-smmonjos-mvp/

## Estructura del repo

```
index.html                      # app (HTML + JS, icones Lucide inline). És el lloc.
styles.css                      # Tailwind COMPILAT que usa index.html (definició real de
                                #   bg-brand-600, flex, rounded-xl, colors de badge…). VIU.
data/
  agendas.json                  # MANIFEST: llista d'agendes + default (l'última de la llista)
  agenda-setembre-2026.json     # 88 esdeveniments (agenda per defecte)
  agenda-juliol-agost-2026.json # 128 esdeveniments (Festa Major + campus)
  eventos.json                  # FALLBACK (còpia de setembre) si falla agendas.json
scripts/
  ingest.py                     # pipeline LLM (opencode-go / deepseek-v4-pro) -> JSON d'agenda
  extract_pdf_dates.py          # extractor heurístic (sense clau) com a fallback
```

> El lloc **no necessita compilar**: s'obre directament al navegador. No cal `npm install`
> ni `npm run build`. (`node_modules/`, `dist/`, `src/`, configs Vite/React foren el MVP
> inicial i **s'han eliminat**; el codi en producció és aquest estàtic autònom.)

## Com funciona (render)

- `index.html` carrega `data/agendas.json` i mostra **l'última agenda del manifest** per
  defecte (ara: Setembre 2026). El **icono de calendari del títol** obre un popup discret
  per canviar de mes; cada agenda baixa el seu propi PDF.
- Pestanyes (dinàmiques, derivades del JSON, no hardcodejades): `Agenda` (Actes),
  `Formació`, `Esport`, `Notícies`, `Telèfons`.
- **Capçalera:** el **icono de calendari** (esquerra del títol) obre un popup discret per
  canviar de mes; el **icono "i" d'informació** (dreta del títol) obre un banner gris amb
  l'avís de generació (IA + PDF oficial + descàrrec de responsabilitat) que s'auto-oculta.
- Cerca i filtre per dia actuen **dins de la categoria activa**. La targeta obre el detall
  amb un sol toc; `Maps` (blau) i `Compartir` (verd) només al detall. Camps buits no es mostren.
- **Esport** s'agrupa només per `subcategoria` (**Joves i Infants** / **Persones Adultes**),
  sense subsegments per curs. `Formació` manté subagrupacions.

## Dades

Cada esdeveniment (esquema comú a totes les agendes):

`id, seccio, categoria, subcategoria, subsubcategoria, titulo, descripcion, lugar,
fecha_inicio, fecha_fin, hora_inicio, hora_fin, grup, enlace_maps, contactes`

> `subsubcategoria` **no s'usa a Esports** (només `subcategoria` Joves/Adults). En altres
> seccions pot existir segons el PDF d'origen.

Contactes (pestanya Telèfons): `nom, telefon, email, nota, web, grup`.

**Badges de categoria:** el color s'aplica **inline** (`style="background:…;color:…"`) per
garantir visibilitat independent del CSS. Categories amb color definit: `Teatre, Música,
Infantil, Esport, Formació, Cultura, Festes, Gastronomia, Mercats, Serveis` (+ fallback
gris `Altres` si en falta). Icones de pestanya: Agenda=calendari, Formació=graduació,
Esport=trofeu, Notícies=periòdic, Telèfons=telèfon. Els esdeveniments **sense data**
apareixen com a "Avís" a Notícies.

**Regles de manteniment (projecte):**
- **Mai "Altres" com a agrupació.** Si un element no encaixa en una subcategoria real,
  `null` i es llista directe sota el grup pare.
- **Month-agnostic:** el codi no coneix noms concrets de grups/categories; el render els
  deriva del propi JSON. Regenerar el JSON d'un altre mes no requereix tocar `index.html`.

## Afegir / regenerar un mes

El PDF de cada mes té **layout diferent** (setembre = seccions; juliol-agost = calendari
per dia + Festa Major). Per tant no hi ha un sol extractor perfecte; el camí recomanat:

1. **Via OpenClaw (recomanat):** delegar a un subagent amb `deepseek-v4-pro` que llegeixi
   el PDF i escrigui `data/agenda-<mes>.json` seguint l'esquema de
   `agenda-setembre-2026.json`. (El script sol contra `opencode.ai` rep **403 de Cloudflare**
   perquè no porta la sessió legítima d'opencode; dins OpenClaw sí funciona.)
2. **Via script (si tens la clau i sessió):** `python3 scripts/ingest.py --out
   data/agenda-<mes>.json --pdf-url <URL> --mes "<Mes Any>"` (necessita
   `OPENCODE_API_KEY`). `scripts/extract_pdf_dates.py` és l'extractor heurístic sense clau
   (útil només per PDFs senzills; per Festa Major és incomplet).

Després: afegeix l'entrada a `data/agendas.json` (l'última de la llista és la que carrega
per defecte) i fes `git push`.

**Font oficial:** les agendes en PDF es publiquen a la **web municipal** a
https://www.santamargaridaielsmonjos.cat/actualitat/publicacions-locals/agenda-municipal
(el banner d'informació de la capçalera hi enllaça a la web). Els JSON es generen a
partir d'aquests PDF.

**Seguretat de dades:** `ingest.py` fa backup (`.bak`) abans de sobreescriure i **no
destrueix** l'arxiu existent si falla. (Els `.bak` són artefactes locals i **no es
versionen**.)

## Desplegament

GitHub Pages amb **Source: Deploy from a branch → `main`** (arrel). Qualsevol `git push`
a `main` publica. No s'usa GitHub Actions (el workflow de `legacy/` s'ha eliminat).
Cache de Pages `max-age=600`: el lloc trenca la memòria cau amb `?v=N` a la URL.

## Telegram Mini App

`index.html` detecta `window.Telegram?.WebApp`: si existeix crida `ready()`/`expand()`;
si no, es renderitza com a web estàndard. El mateix codi serveix per a tots dos destins.
