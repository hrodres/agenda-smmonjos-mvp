#!/usr/bin/env python3
"""
Check diari de la pàgina d'agendes del Ajuntament de Santa Margarida i els Monjos.

- Fa fetch de la pàgina d'agendes municipals.
- Detecta el PDF del MES NOU (el més recent que encara NO està a data/agendas.json
  i que és posterior al mes per defecte actual).
- Si NO hi ha cap mes nou -> NO IMPRIMEIX RES (job silenciós, no molesta).
- Si hi ha mes nou -> el processa:
    1. Descarrega el PDF i en treu el text (pdfplumber).
    2. Crida opencode-go/deepseek-v4-pro VIA EL GATEWAY d'OpenClaw (el camí que
       funciona) per generar el JSON estructurat.
    3. Aplica les regles: Esport només per subcategoria (Joves i Infants /
       Persones Adultes), sense subsubcategoria; títols originals; esquema acordat.
    4. Escriu data/agenda-<mes>.json, sincronitza eventos.json, actualitza
       agendas.json (el nou mes passa a ser el defecte) i fa commit + push a GitHub.
    5. Imprimeix un resum (el job cron l'entrega per Telegram).

Només pusheja si el JSON té >=50 events (guarda de dades dolentes). Si falla, no
toca res del repo.
"""
from __future__ import annotations
import os, re, sys, json, subprocess, datetime
from html import unescape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Octubre 2026: la web municipal va canviar d'estructura. L'antic
# /actualitat/publicacions-locals/agenda-municipal retorna 404. Ara hi ha un
# CATÀLEG paginat de targetes (1..N); cada targeta enllaça a una subpàgina
# .html i el PDF viu DINS d'aquesta subpàgina, no al llistat.
BASE_URL = "https://www.santamargaridaielsmonjos.cat"
SUB_PATH = "/actualitat-i-publicacions/cataleg-de-publicacions/agenda-mensual"
PAGE = BASE_URL + SUB_PATH
MODEL = "opencode-go/deepseek-v4-pro"
SESSION_KEY = "agent:main:agenda-proc"
MIN_EVENTS = 50

MESES = {
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12,
}


def fetch_html(url: str) -> str:
    import requests
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (OpenClaw agenda-check)"})
    r.raise_for_status()
    return r.text


def resoldre_binari_openclaw() -> str | None:
    """Retorna la ruta absoluta del CLI `openclaw`, o None si no en troba cap.

    El planificador no carrega nvm: el seu PATH és
    /usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin i `sh` és dash,
    així que ~/.bashrc (l'únic que fa source de nvm.sh) no s'executa mai.
    Invocar "openclaw" a seques donava FileNotFoundError sota el cron.
    """
    import shutil
    candidats = [
        os.environ.get("OPENCLAW_BIN"),
        shutil.which("openclaw"),
        "/root/.nvm/versions/node/v26.8.2/bin/openclaw",
        "/root/.openclaw/tmp/agent-cli/openclaw",
        "/usr/local/bin/openclaw",
    ]
    for c in candidats:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


# Sòl·lids de URL per mes (sense accents: 'març' -> 'marc').
SLUG_MES = {
    "gener": "gener", "febrer": "febrer", "març": "marc", "abril": "abril",
    "maig": "maig", "juny": "juny", "juliol": "juliol", "agost": "agost",
    "setembre": "setembre", "octubre": "octubre", "novembre": "novembre",
    "desembre": "desembre",
}


def agendes_per_sondeig(mesos_enrere: int = 2, mesos_endavant: int = 2) -> list[dict]:
    """Descobreix agendes provant URLs, sense dependre del catàleg paginat.

    El catàleg va deixar de llistar els mesos recents (nov. 2026: només arriba
    a 'Agenda juny 2026'), però la subpàgina del mes SÍ que existeix i respon
    200. Es prova el patró d'URL directament.
    """
    avui = datetime.date.today()
    inv = {v: k for k, v in MESES.items()}
    out = []
    for delta in range(-mesos_enrere, mesos_endavant + 1):
        idx = avui.year * 12 + (avui.month - 1) + delta
        any_, mes = divmod(idx, 12)
        mes += 1
        nom = inv.get(mes)
        if not nom:
            continue
        slug = SLUG_MES.get(nom, nom)
        url = f"{BASE_URL}/actualitat-i-publicacions/agenda-mensual/agenda-{slug}-{any_}.html"
        try:
            page = fetch_html(url)
        except Exception:
            continue
        if "agenda" not in page.lower():
            continue
        item = _agenda_item(f"Agenda {nom} {any_}", url)
        if item:
            out.append(item)
    return out


def parse_agendes(html: str):
    """Retorna llista de dicts {id, label, url, key} ordenats per key descendent.

    Estructura NOVA (oct. 2026): cada agenda és una targeta amb una imatge i un
    enllaç a una subpàgina de detall. El PDF no és al llistat.

        <a href="https://.../agenda-mensual/agenda-juny-2026.html">
            <img src="..." alt="Agenda juny 2026">

    S'accepta també el format ANTIC (enllaç directe a un .pdf amb el text
    'Agenda <mes>') perquè si algun dia barregen els dos, no es perdi res.
    """
    out = []
    seen = set()

    # --- format nou: targeta amb imatge + alt ---
    pat_card = re.compile(
        r'<a\s+href="([^"]+?)"[^>]*>\s*<img[^>]*alt="([^"]*)"',
        re.I | re.S)
    for m in pat_card.finditer(html):
        href, alt = m.group(1), m.group(2)
        if "/agenda-mensual/" not in href:
            continue  # navegació, no una agenda
        label = " ".join(unescape(alt).split())
        if "agenda" not in label.lower():
            continue
        item = _agenda_item(label, href)
        if item and item["id"] not in seen:
            seen.add(item["id"])
            out.append(item)

    # --- format antic: enllaç directe al PDF ---
    pat_pdf = re.compile(r'href="(https://[^"]+\.pdf)"[^>]*>\s*Agenda\s+([^<]+)</a>', re.I)
    for m in pat_pdf.finditer(html):
        url, label = m.group(1), " ".join(m.group(2).split())
        item = _agenda_item(label, url)
        if item and item["id"] not in seen:
            seen.add(item["id"])
            out.append(item)

    out.sort(key=lambda x: x["key"], reverse=True)
    return out


def _agenda_item(label: str, url: str):
    """Converteix 'Agenda juny 2026' + URL en {id, label, url, key} o None."""
    tokens = re.findall(r"[A-Za-zçàèéíòóúü·]+|\d{4}", label)
    mesos = [t.lower() for t in tokens if t.lower() in MESES]
    anys = [int(t) for t in tokens if t.isdigit() and len(t) == 4]
    if not mesos or not anys:
        return None
    any_ = anys[0]
    key = any_ * 12 + MESES[mesos[0]]
    mid = "-".join(mesos) + f"-{any_}"
    # El `alt` de la targeta diu 'Agenda novembre 2026'; els altres mesos (format
    # antic) ja perdien el prefix perque el regex el consumia. S'elimina aqui per
    #que tots els labels quedin igual: 'Novembre 2026', no 'Agenda novembre 2026'.
    lab = re.sub(r"^\s*agenda\s+", "", label, flags=re.I).strip()
    lab = lab[0].upper() + lab[1:] if lab else lab
    return {"id": mid, "label": lab, "url": url, "key": key}


def catalog_pages(html: str) -> int:
    """Quantes pàgines té el catàleg (llegeix 'N pàgines' del paginador)."""
    m = re.search(r'(\d+)\s*p[àa]gines', html, re.I)
    return int(m.group(1)) if m else 1


def totes_les_agendes() -> list[dict]:
    """Recorre TOT el catàleg paginat i retorna les agendes ordenades.

    El mes més recent és a la pàgina 1, però es recorren totes perquè el
    `key` calculat (no l'ordre del HTML) és qui mana.
    """
    first = fetch_html(PAGE)
    n = catalog_pages(first)
    items = {i["id"]: i for i in parse_agendes(first)}
    for pag in range(2, min(n, 12) + 1):
        try:
            sub = fetch_html(f"{PAGE}?pag={pag}")
        except Exception:
            break
        for i in parse_agendes(sub):
            items.setdefault(i["id"], i)
    return sorted(items.values(), key=lambda x: x["key"], reverse=True)


def resoldre_pdf(item: dict) -> str | None:
    """Retorna la URL absoluta del PDF d'una agenda.

    Si `url` ja és un PDF, es retorna tal qual (format antic). Si és una
    subpàgina de detall, s'hi busca l'enllaç al document.
    """
    url = item["url"]
    if url.lower().endswith(".pdf"):
        return url
    if not url.startswith("http"):
        url = BASE_URL + ("" if url.startswith("/") else "/") + url
    try:
        page = fetch_html(url)
    except Exception:
        return None
    # El document pot aparèixer com a href directe o dins d'un visor /pdf?file=
    m = re.search(r'href="(/media/repository/import/documents/[^"]+\.pdf)"', page, re.I)
    if m:
        return BASE_URL + m.group(1)
    m = re.search(r'/pdf\?file=(/media/repository/[^"&]+)', page, re.I)
    if m:
        return BASE_URL + m.group(1)
    m = re.search(r'href="(https?://[^"]+\.pdf)"', page, re.I)
    if m:
        return m.group(1)
    return None


def ya_processats() -> dict:
    p = os.path.join(REPO, "data", "agendas.json")
    return json.load(open(p, encoding="utf-8"))


def detectar_nou(html: str | None = None) -> dict | None:
    """Retorna l'agenda més recent que encara no és al manifest, o None.

    Compara per `key` (any*12+mes), no per ordre del HTML: el catàleg nou
    barreja targetes i pot repetir el mateix mes en diverses pàgines.
    """
    ags = ya_processats()
    ids = {a["id"] for a in ags.get("agendas", [])}
    defkey = 0
    for a in ags.get("agendas", []):
        mm = re.match(r"(\w+)-(\d{4})$", a["id"])
        if mm and mm.group(1) in MESES:
            defkey = max(defkey, int(mm.group(2)) * 12 + MESES[mm.group(1)])
    candidates = totes_les_agendes() if html is None else parse_agendes(html)
    for cand in candidates:
        if cand["id"] in ids:
            continue  # ja el tenim
        if cand["key"] > defkey:
            return cand  # mes nou, endavant
        break  # els seguents son mes vells -> cap nou
    return None


def detectar_nou_sondeig() -> dict | None:
    """Com `detectar_nou`, però descobrint els mesos provant URLs.

    El catàleg paginat ja no llista els mesos recents (nov. 2026: arriba només
    a 'Agenda juny 2026'), de manera que `detectar_nou` no veia l'agenda nova
    encara que la subpàgina existís.
    """
    ags = ya_processats()
    ids = {a["id"] for a in ags.get("agendas", [])}
    defkey = 0
    for a in ags.get("agendas", []):
        mm = re.match(r"(\w+)-(\d{4})$", a["id"])
        if mm and mm.group(1) in MESES:
            defkey = max(defkey, int(mm.group(2)) * 12 + MESES[mm.group(1)])
    for cand in sorted(agendes_per_sondeig(), key=lambda x: x["key"], reverse=True):
        if cand["id"] in ids:
            continue
        if cand["key"] > defkey:
            return cand
    return None


def extreure_text_pdf(url: str) -> str:
    import requests, pdfplumber, tempfile
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
    blocs = []
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages):
            t = pg.extract_text() or ""
            blocs.append(f"--- PÀGINA {i+1} ---\n{t}")
    os.remove(path)
    return "\n\n".join(blocs)


PROMPT_SCHEMA = """Ets un extractor d'agendes municipals a Catalunya. Reps el text extret
d'un PDF d'agenda (maquetat en columnes). Retorna NOMÉS un objecte JSON vàlid (sense markdown,
sense text al voltant) que compleixi aquest esquema:

{
  "eventos": [
    {"titulo":str,"fecha_inicio":str "YYYY-MM-DD","fecha_fin":str|null "YYYY-MM-DD o null",
     "hora_inicio":str|null "HH:MM 24h o null","hora_fin":str|null,
     "lugar":str,"categoria":str,"seccio":str|null "Actes|Formació|Esports|Notícies",
     "subcategoria":str|null,"subsubcategoria":str|null,"precio_socios":str|null,
     "precio_general":str|null,"descripcion":str,
     "actividades":[{"nombre":str,"horario":str|null,"lugar":str|null}]|null,
     "enlace_maps":str "URL Google Maps search URL-encoded"}
  ],
  "contactes":[{"nom":str,"telefon":str,"email":str|null,"nota":str|null,"web":str|null,"grup":str|null}]
}

REGLES:
- 'seccio': Actes / Formació / Esports / Notícies segons el PDF. Els serveis sense data -> Notícies.
- 'categoria' en català (Teatre, Música, Infantil, Esport, Formació, Cultura, Festes,
  Gastronomia, Mercats, Serveis, Altres...).
- DINS 'Formació' i 'Esport', el PDF fa servir sub-capçaleres (ex: 'Cursos i Activitats',
  'Cant Coral', 'Joves i Infants', 'Persones Adultes', 'Servei Local d'Ocupació'). Posa-les a
  'subcategoria'. SEGON NIVELL (ex: '3r i 4t de primària', 'Manualitats de Dona al Dia') a
  'subsubcategoria', EXCEPTE a ESPORT: allà 'subsubcategoria' SEMPRE null (només Joves i Infants
  / Persones Adultes).
- EXPOSICIONS: els esdeveniments sota la sub-capçalera 'Exposicions' del PDF (exposicions,
  galeries, mostres d'art) → 'seccio': 'Actes', 'categoria': 'Cultura', 'subcategoria': 'Exposicions'.
- Si un element no encaixa en cap grup: subcategoria/subsubcategoria a null. MAI 'Altres'.
- 'actividades': QUAN un event agrupa diverses activitats amb horari/lloc propi (típic de
  ESPORTS: 'Joves i Infants 2026-2027' i 'Persones Adultes 2026-2027'), desglossa CADA
  activitat amb el seu horari i lloc EXACTES del PDF (nom: l'activitat; horario: dies i hores;
  lugar: espai). Si no hi ha activitats desglossables → null. Mai inventar dades.
- 'enlace_maps': https://www.google.com/maps/search/?api=1&query=<lloc>+Santa+Margarida+i+els+Monjos (URL-encoded).
- Inclou TOTS els esdeveniments i els contactes de la pàgina de Telèfons d'interès.
- Només el JSON, res més."""


def generar_json(text: str, label: str, parte: str = "") -> dict | None:
    prompt_path = "/tmp/agenda_prompt.txt"
    instr = ("\n\n" + parte) if parte else ""
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(PROMPT_SCHEMA + instr + "\n\nAGENDA: " + label + "\n\nTEXT DEL PDF:\n" + text)
    # El planificador no hereta nvm: cal la ruta absoluta o FileNotFoundError.
    binari = resoldre_binari_openclaw()
    if not binari:
        print("ERROR: no s'ha trobat el binari 'openclaw' (OPENCLAW_BIN / nvm / shim).")
        return None
    try:
        r = subprocess.run(
            [binari, "agent", "--model", MODEL, "--session-key", SESSION_KEY,
             "--message-file", prompt_path, "--json", "--timeout", "2400", "--thinking", "off"],
            capture_output=True, text=True, timeout=2400,
        )
    except Exception as e:
        print("ERROR crida agent:", e)
        return None
    if r.returncode != 0:
        print("Agent error:", r.stderr[:500])
        return None
    try:
        out = json.loads(r.stdout)
        txt = out["result"]["payloads"][0]["text"]
    except Exception as e:
        print("No puc parsejar la sortida de l'agent:", e)
        return None
    # extreure el primer JSON
    s = txt.find("{")
    e = txt.rfind("}")
    if s == -1 or e == -1:
        print("L'agent no ha retornat JSON.")
        return None
    try:
        return json.loads(txt[s:e + 1])
    except Exception as e:
        print("JSON invàlid:", e)
        return None


# Exposicions per paraula clau (rescat quan el LLM no les categoritza). 'mostra'
# només si va seguida de terme artístic (evita 'Mostra de bestiar' de la Fira
# de la Transhumància); 'homenatge'/'col·lecció' no xoquen amb cap event actual.
EXPO_RE = re.compile(
    r"exposic|palmadotze|homenatge|col\.?leccio|"
    r"mostra\s+(?:d'|de\s+)?(?:art|pintura|fotograf|dibuix|escultura|il·lustra)",
    re.I)


def actualizar_titulo_mes(label: str) -> None:
    """La vista prèvia en compartir (Telegram/WhatsApp) llegeix el <title> i els
    <meta> ESTÀTICS del head — el JS no s'executa. Regenera el mes al head abans
    del commit perquè la preview mai no quedi amb un mes antic."""
    path = os.path.join(REPO, "index.html")
    html = open(path, encoding="utf-8").read()
    label = " ".join(label.split())
    mes_lower = label.lower()
    html2 = re.sub(r'<meta name="description" content="[^"]*" />',
                   f'<meta name="description" content="Agenda municipal de Santa Margarida i els Monjos — {mes_lower}." />',
                   html, count=1)
    html2 = re.sub(r'<meta property="og:title" content="[^"]*" />',
                   f'<meta property="og:title" content="Agenda SMMonjos · {label}" />', html2, count=1)
    html2 = re.sub(r'<meta property="og:description" content="[^"]*" />',
                   f'<meta property="og:description" content="Agenda municipal de Santa Margarida i els Monjos — {mes_lower}." />', html2, count=1)
    html2 = re.sub(r'<title>Agenda SMMonjos · [^<]*</title>',
                   f'<title>Agenda SMMonjos · {label}</title>', html2, count=1)
    if html2 != html:
        open(path, "w", encoding="utf-8").write(html2)
        print(f"Títol del head actualitzat a '{label}'.")


def carregar_anteriors() -> list[dict]:
    """JSONs dels mesos ja processats (fins a 3), per comparar volums."""
    try:
        ags = ya_processats()
    except Exception:
        return []
    prevs = []
    for a in ags.get("agendas", [])[-3:]:
        path = os.path.join(REPO, "data", a.get("file") or "")
        if path.endswith(".json") and os.path.exists(path):
            try:
                prevs.append(json.load(open(path, encoding="utf-8")))
            except Exception:
                continue
    return prevs


def check_anomalia(d: dict, prevs: list[dict]) -> list[str]:
    """Retorna llistat d'avisos. Un avís que comença per 'BLOQUEIG:' impedeix el
    push (el LLM pot truncar/ometre si el PDF creix o canvia de format). Els
    AVÍS de secció no bloquegen (una secció pot desaparèixer legítimament: Festa
    Major, escola d'estiu...)."""
    avisos = []
    if not prevs:
        return avisos
    totals = [len(p.get("eventos", [])) for p in prevs if p.get("eventos")]
    if not totals:
        return avisos
    mitjana = sum(totals) / len(totals)
    n = len(d.get("eventos", []))
    if n < 0.6 * mitjana:
        avisos.append(
            f"BLOQUEIG: {n} events nous vs mitjana {mitjana:.0f} dels últims mesos "
            "(<60%). Possible extracció incompleta del PDF. Revisa abans de pushear.")
    # Per secció: avís si una secció sòlida del mes anterior desapareix de cop.
    def per_seccio(dd: dict) -> dict:
        c: dict = {}
        for e in dd.get("eventos", []):
            s = e.get("seccio") or "(sense secció)"
            c[s] = c.get(s, 0) + 1
        return c
    c_prev, c_new = per_seccio(prevs[-1]), per_seccio(d)
    for s, n2 in c_prev.items():
        if n2 >= 5 and c_new.get(s, 0) == 0:
            avisos.append(f"AVÍS: la secció '{s}' passa de {n2} events a 0 aquest mes. Revisa si el PDF la porta.")
    return avisos


def aplicar_regles(d: dict) -> dict:
    vistos = set()
    for ev in d.get("eventos", []):
        if ev.get("seccio") == "Esports":
            ev["subsubcategoria"] = None
        # Exposicions -> Cultura + subcategoria 'Exposicions'.
        # No toquem Notícies (ex: 'Bases de la Mostra Artística' és un avís, no un event).
        if ev.get("seccio") != "Notícies" and not ev.get("subcategoria"):
            blob = " ".join(str(ev.get(k) or "") for k in ("titulo", "descripcion"))
            if EXPO_RE.search(blob):
                ev["seccio"] = ev.get("seccio") or "Actes"
                ev["categoria"] = "Cultura"
                ev["subcategoria"] = "Exposicions"
        # Garantir id únic (el frontend obre el modal buscant per id).
        if not ev.get("id"):
            fecha = (ev.get("fecha_inicio") or "").replace("-", "")[:8] or "avis"
            slug = re.sub(r"[^a-z0-9]+", "-", (ev.get("titulo") or "").lower().strip())[:40].strip("-")
            base = f"evt-{fecha}-{slug or 'event'}"
            eid, n = base, 2
            while eid in vistos:
                eid = f"{base}-{n}"
                n += 1
            ev["id"] = eid
        vistos.add(ev["id"])
    return d


def reintentar_push_pendent() -> int | None:
    """Reintenta pujar commits locals que van quedar sense pujar.

    Si un push va fallar, el mes ja consta a agendas.json i `detectar_nou` no
    el tornaria a veure mai: la publicació es perdria en silenci. Es mira
    primer si el repo va per davant d'origin i es reintenta.

    Silenci en cas de fallada a propòsit: mentre no hi hagi credencial, el push
    falla cada dia i avisar-ne cada dia seria soroll amb un problema que no es
    pot resoldre des d'aquí. Quan el token existesqui, el backlog es puja sol.
    """
    try:
        rev = subprocess.run(
            ["git", "-C", REPO, "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True, text=True, timeout=60)
        ahead = int((rev.stdout or "0").strip() or 0) if rev.returncode == 0 else 0
    except Exception:
        return None
    if ahead <= 0:
        return None
    try:
        subprocess.run(["git", "-C", REPO, "push", "origin", "main"],
                       check=True, capture_output=True, text=True, timeout=180)
        print(f"PUSH PENDENT RESOLT: {ahead} commit(s) pujats.")
    except Exception:
        pass  # silenci: es reintentarà demà sense avisar
    return None


def main() -> int:
    # Si un push anterior va quedar pendent, es reintenta abans de res: el mes
    # ja consta a agendas.json i no es tornaria a veure mai.
    # NO bloqueja: amb el push trencat de forma permanent, aturar-se aquí voldria
    # dir no processar mai cap mes nou. Només s'ha d'informar i continuar.
    reintentar_push_pendent()

    # El catàleg paginat funciona i és la font oficial, així que mana ell.
    # El sondeig d'URLs queda NOMÉS com a xarxa de seguretat per si el catàleg
    # deixa de llistar els mesos recents (ja va passar: nov. 2026 va trigar).
    nou = detectar_nou()
    if not nou:
        nou = detectar_nou_sondeig()
    if not nou:
        return 0  # silenci: cap mes nou

    # A la web nova l'enllaç de la targeta és una subpàgina .html i el PDF viu
    # a dins. `resoldre_pdf` cobreix també el format antic (enllaç directe).
    pdf_url = resoldre_pdf(nou)
    if not pdf_url:
        print(f"NOU MES DETECTAT però sense PDF localitzable: {nou['label']} -> {nou['url']}")
        return 1
    print(f"NOU MES DETECTAT: {nou['label']} -> {pdf_url}")
    text = extreure_text_pdf(pdf_url)

    # La agenda completa no cap en una sola resposta del model (stopReason=length ~60KB):
    # partim el text del PDF en dues meitats i fem dues crides LLM, després fusionem.
    MARCA = "\n\n--- PÀGINA "
    parts = text.split(MARCA)  # parts[0] = preàmbul; parts[1..] = pàgines
    if len(parts) >= 3:
        meitat = (len(parts) - 1 + 1) // 2
        p1 = parts[0] + MARCA + MARCA.join(parts[1:1 + meitat])
        p2 = parts[0] + MARCA + MARCA.join(parts[1 + meitat:])
    else:
        p1, p2 = text, ""

    d1 = generar_json(
        p1, nou["label"],
        "AQUESTA ÉS LA PRIMERA MEITAT DEL PDF. Retorna NOMÉS els esdeveniments "
        "d'aquesta part (sense contactes).")
    d2 = None
    if p2.strip():
        d2 = generar_json(
            p2, nou["label"],
            "AQUESTA ÉS LA SEGONA MEITAT DEL PDF. Retorna els esdeveniments restants "
            "d'aquesta part i TOTS els contactes de la pàgina de Telèfons d'interès.")

    d = {"eventos": [], "contactes": []}
    if d1:
        d["eventos"] += d1.get("eventos", [])
        d["contactes"] += d1.get("contactes", []) or []
    if d2:
        d["eventos"] += d2.get("eventos", [])
        d["contactes"] += d2.get("contactes", []) or []
    if not d or len(d.get("eventos", [])) < MIN_EVENTS:
        print(f"Resultat insuficient ({len(d.get('eventos',[]))} events); no es toca res.")
        return 1
    d = aplicar_regles(d)

    # Blindatge anti-omissió: si el volum cau molt respecte als últims mesos, no
    # toquem res (el LLM pot haver truncat/omès). AGENDA_FORCE=1 salta el bloqueig.
    if os.environ.get("AGENDA_FORCE") != "1":
        avisos = check_anomalia(d, carregar_anteriors())
        for av in avisos:
            print("ANOMALIA:", av)
        if any(av.startswith("BLOQUEIG") for av in avisos):
            print("No es toca res (anomalia detectada).")
            return 2

    d["municipio"] = "Santa Margarida i els Monjos"
    d["mes"] = nou["label"]
    d["fuente_pdf"] = pdf_url
    d["generado"] = datetime.date.today().isoformat()
    d["generado_por"] = "agenda-check (opencode-go/deepseek-v4-pro via gateway)"
    d["total"] = len(d["eventos"])

    # escriure fitxers
    ev_path = os.path.join(REPO, "data", "eventos.json")
    ag_path = os.path.join(REPO, "data", "agenda-" + nou["id"] + ".json")
    json.dump(d, open(ev_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(d, open(ag_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # actualitzar agendas.json (nou = defecte)
    ags = ya_processats()
    for a in ags.get("agendas", []):
        a["default"] = False
    ags["agendas"].append({
        "id": nou["id"], "label": nou["label"], "file": "agenda-" + nou["id"] + ".json",
        "pdf": pdf_url, "default": True,
        "fuente": "extraccio completa (LLM deepseek-v4-pro via gateway OpenClaw)",
    })
    ags["default"] = nou["id"]
    json.dump(ags, open(os.path.join(REPO, "data", "agendas.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # La preview en compartir llegeix el head estàtic: regenerar-lo amb el mes nou.
    actualizar_titulo_mes(nou["label"])

    # commit + push
    subprocess.run(["git", "-C", REPO, "add", "-A"], check=True)
    subprocess.run(["git", "-C", REPO, "-c", "user.name=hrodres",
                    "-c", "user.email=hrodres@users.noreply.github.com", "commit", "-q",
                    "-m", f"Agenda {nou['label']}: JSON generat (deepseek-v4-pro) + push automàtic"], check=True)
    try:
        subprocess.run(["git", "-C", REPO, "push", "origin", "main"],
                       check=True, capture_output=True, text=True, timeout=180)
    except subprocess.CalledProcessError as e:
        # El JSON ja és al disc i a agendas.json: es reintentarà a la següent
        # execució via reintentar_push_pendent().
        print(f"PROCESSAT però PUSH FALLIT: {nou['label']} — {len(d['eventos'])} events.")
        print("  detall:", (e.stderr or "")[:300].replace("\n", " "))
        print("  es reintentarà a la propera execució.")
        return 1
    print(f"PROCESSAT i PUSHEJAT: {nou['label']} — {len(d['eventos'])} events, "
          f"{len(d.get('contactes', []))} contactes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
