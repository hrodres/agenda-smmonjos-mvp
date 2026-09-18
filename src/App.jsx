import { useEffect, useMemo, useState } from 'react'
import {
  CalendarDays,
  Clock,
  MapPin,
  Music,
  Theater,
  Baby,
  Dumbbell,
  GraduationCap,
  Sparkles,
  Search,
  X,
  ExternalLink,
  MapPinned,
  UtensilsCrossed,
  ArrowLeft,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Constants (català)
// ---------------------------------------------------------------------------
const CATEGORIAS = ['Totes', 'Teatre', 'Música', 'Infantil', 'Esport', 'Formació', 'Altres']

const CAT_META = {
  Teatre: { icon: Theater, classes: 'bg-rose-100 text-rose-700', dot: 'bg-rose-500' },
  Música: { icon: Music, classes: 'bg-violet-100 text-violet-700', dot: 'bg-violet-500' },
  Infantil: { icon: Baby, classes: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  Esport: { icon: Dumbbell, classes: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  Formació: { icon: GraduationCap, classes: 'bg-sky-100 text-sky-700', dot: 'bg-sky-500' },
  Altres: { icon: Sparkles, classes: 'bg-slate-100 text-slate-700', dot: 'bg-slate-500' },
}

const MESES = ['', 'Gen', 'Febr', 'Març', 'Abr', 'Maig', 'Juny', 'Jul', 'Ag', 'Set', 'Oct', 'Nov', 'Des']

function fmtFecha(iso) {
  if (!iso) return ''
  const [y, m, d] = iso.split('-').map(Number)
  return { dia: d, mes: MESES[m] || '', any: y }
}

// ---------------------------------------------------------------------------
// Hook: detecció nativa del SDK de Telegram
// ---------------------------------------------------------------------------
function useTelegram() {
  const [tg, setTg] = useState(null)
  useEffect(() => {
    const webapp = typeof window !== 'undefined' ? window.Telegram?.WebApp : null
    if (webapp) {
      try {
        webapp.ready?.()
        webapp.expand?.() // es integra com a Mini App a pantalla completa
        webapp.setHeaderColor?.('#1a5fd0')
        webapp.setBackgroundColor?.('#f4f6fb')
      } catch (e) {
        /* no crític */
      }
      setTg(webapp)
    }
  }, [])
  return tg
}

// ---------------------------------------------------------------------------
// Components d'UI
// ---------------------------------------------------------------------------
function Header({ municipio, mes, search, setSearch }) {
  return (
    <div className="pt-safe sticky top-0 z-20 bg-brand-600 text-white shadow-lg">
      <div className="px-4 pt-3 pb-3">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-6 w-6 shrink-0" />
          <div className="leading-tight">
            <h1 className="text-lg font-extrabold tracking-tight">Agenda {municipio}</h1>
            <p className="text-[11px] font-medium text-brand-100">{mes}</p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 rounded-xl bg-white/15 px-3 py-2 ring-1 ring-white/20">
          <Search className="h-4 w-4 text-brand-100" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cerca per títol, lloc o paraula…"
            className="w-full bg-transparent text-sm text-white placeholder:text-brand-100 focus:outline-none"
            inputMode="search"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              aria-label="Neteja"
              className="rounded-full p-1 text-brand-100 hover:bg-white/10"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Filtres({ activa, setActiva }) {
  return (
    <div className="sticky top-[104px] z-10 -mx-4 flex gap-2 overflow-x-auto px-4 py-2 scroll-area bg-[#f4f6fb]/95 backdrop-blur">
      {CATEGORIAS.map((c) => {
        const sel = c === activa
        return (
          <button
            key={c}
            onClick={() => setActiva(c)}
            className={
              'whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-semibold transition ' +
              (sel
                ? 'bg-brand-600 text-white shadow'
                : 'bg-white text-slate-600 ring-1 ring-slate-200')
            }
          >
            {c}
          </button>
        )
      })}
    </div>
  )
}

function SponsorBanner() {
  return (
    <a
      href="https://www.santamargaridaielsmonjos.cat/"
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-2xl bg-gradient-to-br from-amber-400 via-orange-400 to-rose-400 p-[1.5px] shadow-card"
    >
      <div className="flex items-center gap-3 rounded-2xl bg-white px-4 py-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-rose-400 text-white">
          <UtensilsCrossed className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-bold uppercase tracking-wide text-orange-600">
            Patrocinador · On menjar
          </p>
          <p className="truncate text-sm font-bold text-slate-800">
            On sopar aquest cap de setmana?
          </p>
          <p className="truncate text-xs text-slate-500">
            Descobreix els restaurants del poble · Espai B2B
          </p>
        </div>
        <ExternalLink className="h-4 w-4 shrink-0 text-slate-400" />
      </div>
    </a>
  )
}

function EventCard({ ev, onOpen }) {
  const meta = CAT_META[ev.categoria] || CAT_META.Altres
  const Icon = meta.icon
  const f = fmtFecha(ev.fecha_inicio)
  const hora = ev.hora_inicio
    ? ev.hora_fin
      ? `${ev.hora_inicio} – ${ev.hora_fin}`
      : `A les ${ev.hora_inicio}`
    : ''
  const preu = ev.precio_general
    ? ev.precio_socios
      ? `Socis: ${ev.precio_socios} · General: ${ev.precio_general}`
      : `${ev.precio_general}`
    : ev.precio_socios
    ? ev.precio_socios
    : 'Entrada lliure'

  return (
    <article className="overflow-hidden rounded-2xl bg-white shadow-card ring-1 ring-slate-100">
      <div className="flex">
        {/* data */}
        <div className="flex w-14 shrink-0 flex-col items-center justify-center bg-brand-50 py-3 text-brand-700">
          <span className="text-xl font-extrabold leading-none">{f.dia}</span>
          <span className="text-[11px] font-semibold uppercase">{f.mes}</span>
        </div>
        <div className="min-w-0 flex-1 p-3">
          <div className="mb-1 flex items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${meta.classes}`}>
              <Icon className="h-3 w-3" />
              {ev.categoria}
            </span>
          </div>
          <h3 className="line-clamp-2 text-[15px] font-bold leading-snug text-slate-800">{ev.titulo}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
            {hora && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" /> {hora}
              </span>
            )}
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> {ev.lugar}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={() => onOpen(ev)}
              className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700"
            >
              Veure detalls
            </button>
            <a
              href={ev.enlace_maps}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
            >
              <MapPinned className="h-3.5 w-3.5" /> Maps
            </a>
          </div>
          <p className="mt-1.5 text-[11px] font-medium text-slate-400">{preu}</p>
        </div>
      </div>
    </article>
  )
}

function EventModal({ ev, onClose }) {
  const meta = CAT_META[ev.categoria] || CAT_META.Altres
  const Icon = meta.icon
  const fh = fmtFecha(ev.fecha_fin && ev.fecha_fin !== ev.fecha_inicio ? ev.fecha_fin : null)
  const fi = fmtFecha(ev.fecha_inicio)
  const rang =
    fh && fh.dia
      ? `${fi.dia} ${fi.mes} – ${fh.dia} ${fh.mes} ${fi.any}`
      : `${fi.dia} ${fi.mes} ${fi.any}`

  return (
    <div className="fixed inset-0 z-30 flex items-end justify-center bg-slate-900/50 sm:items-center" onClick={onClose}>
      <div
        className="max-h-[88vh] w-full overflow-y-auto rounded-t-3xl bg-white pb-safe shadow-2xl sm:max-w-md sm:rounded-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between bg-white/95 px-4 py-3 backdrop-blur">
          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${meta.classes}`}>
            <Icon className="h-3.5 w-3.5" /> {ev.categoria}
          </span>
          <button onClick={onClose} aria-label="Tanca" className="rounded-full p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-4 pb-5">
          <h2 className="text-xl font-extrabold leading-tight text-slate-800">{ev.titulo}</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-brand-600" />
              <span>{rang}</span>
            </div>
            {ev.hora_inicio && (
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-brand-600" />
                <span>
                  {ev.hora_fin ? `${ev.hora_inicio} – ${ev.hora_fin}` : `A les ${ev.hora_inicio}`}
                </span>
              </div>
            )}
            <div className="flex items-start gap-2">
              <MapPin className="mt-0.5 h-4 w-4 text-brand-600" />
              <span>{ev.lugar}</span>
            </div>
            {(ev.precio_general || ev.precio_socios) && (
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600">
                {ev.precio_socios && <div>Socis: {ev.precio_socios}</div>}
                {ev.precio_general && <div>General: {ev.precio_general}</div>}
              </div>
            )}
            {!ev.precio_general && !ev.precio_socios && (
              <div className="rounded-lg bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600">
                Entrada lliure
              </div>
            )}
          </div>
          {ev.descripcion && (
            <p className="mt-3 text-sm leading-relaxed text-slate-600">{ev.descripcion}</p>
          )}
          <div className="mt-4 flex gap-2">
            <a
              href={ev.enlace_maps}
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              <MapPinned className="h-4 w-4" /> Obre a Google Maps
            </a>
            <button
              onClick={onClose}
              className="inline-flex items-center justify-center gap-1 rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-200"
            >
              <ArrowLeft className="h-4 w-4" /> Tornar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
export default function App() {
  useTelegram()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [cat, setCat] = useState('Totes')
  const [obert, setObert] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/eventos.json`, { cache: 'no-store' })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d) => setData(d))
      .catch((e) => setError(String(e)))
  }, [])

  const events = data?.eventos || []

  const filtrats = useMemo(() => {
    const q = search.trim().toLowerCase()
    return events
      .filter((e) => (cat === 'Totes' ? true : e.categoria === cat))
      .filter((e) => {
        if (!q) return true
        return (
          e.titulo.toLowerCase().includes(q) ||
          e.lugar.toLowerCase().includes(q) ||
          (e.descripcion || '').toLowerCase().includes(q) ||
          (e.categoria || '').toLowerCase().includes(q)
        )
      })
      .sort((a, b) => (a.fecha_inicio + (a.hora_inicio || '')).localeCompare(b.fecha_inicio + (b.hora_inicio || '')))
  }, [events, search, cat])

  return (
    <div className="mx-auto flex min-h-full max-w-md flex-col bg-[#f4f6fb]">
      <Header municipio={data?.municipio || 'i els Monjos'} mes={data?.mes || 'Setembre 2026'} search={search} setSearch={setSearch} />
      <div className="px-4">
        <Filtres activa={cat} setActiva={setCat} />
      </div>

      <main className="flex-1 space-y-3 px-4 pb-6 pt-1">
        <SponsorBanner />

        {error && (
          <div className="rounded-2xl bg-rose-50 p-4 text-sm text-rose-700 ring-1 ring-rose-100">
            No s'ha pogut carregar la base de dades ({error}). Torna-ho a provar més tard.
          </div>
        )}

        {!data && !error && (
          <div className="py-10 text-center text-sm text-slate-400">Carregant agenda…</div>
        )}

        {data && filtrats.length === 0 && (
          <div className="py-10 text-center text-sm text-slate-400">
            Cap activitat coincideix amb la cerca.
          </div>
        )}

        {filtats.map((ev, i) => (
          <EventCard key={ev.id || i} ev={ev} onOpen={setObert} />
        ))}

        {data && filtrats.length > 0 && (
          <p className="pt-1 text-center text-xs text-slate-400">
            {filtrats.length} activitat{filtrats.length !== 1 ? 's' : ''} · font: web municipal
          </p>
        )}
      </main>

      {obert && <EventModal ev={obert} onClose={() => setObert(null)} />}
    </div>
  )
}
