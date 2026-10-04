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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "https://www.santamargaridaielsmonjos.cat/actualitat/publicacions-locals/agenda-municipal"
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


def parse_agendes(html: str):
    """Retorna llista de dicts {id, label, url, key} ordenats per key descendent."""
    out = []
    # La web municipal serveix anchors HTML: <a href="https://.../fitxer/XXXX/AGENDA....pdf">Agenda <mes> <any></a>
    pat = re.compile(r'href="(https://[^"]+\.pdf)"[^>]*>\s*Agenda\s+([^<]+)</a>', re.I)
    for m in pat.finditer(html):
        url = m.group(1)
        label = " ".join(m.group(2).split())  # normalitza espais
        # mesos en ordre + primer any de 4 xifres (el que acompanya el primer mes)
        tokens = re.findall(r"[A-Za-zçàèéíòóú·]+|\d{4}", label)
        mesos = [t.lower() for t in tokens if t.lower() in MESES]
        anys = [int(t) for t in tokens if t.isdigit() and len(t) == 4]
        if not mesos or not anys:
            continue
        any_ = anys[0]
        key = any_ * 12 + MESES[mesos[0]]
        mid = "-".join(mesos) + f"-{any_}"
        lab = label[0].upper() + label[1:] if label else label
        out.append({"id": mid, "label": lab, "url": url, "key": key})
    out.sort(key=lambda x: x["key"], reverse=True)
    return out


def ya_processats() -> dict:
    p = os.path.join(REPO, "data", "agendas.json")
    return json.load(open(p, encoding="utf-8"))


def detectar_nou(html: str) -> dict | None:
    ags = ya_processats()
    ids = {a["id"] for a in ags.get("agendas", [])}
    # clau del defecte actual
    defkey = 0
    for a in ags.get("agendas", []):
        mm = re.match(r"(\w+)-(\d{4})", a["id"])
        if mm and mm.group(1) in MESES:
            defkey = max(defkey, int(mm.group(2)) * 12 + MESES[mm.group(1)])
    for cand in parse_agendes(html):
        if cand["id"] in ids:
            continue  # ja el tenim
        if cand["key"] > defkey:
            return cand  # mes nou, endavant
        break  # els seguents son mes vells -> cap nou
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
    try:
        r = subprocess.run(
            ["openclaw", "agent", "--model", MODEL, "--session-key", SESSION_KEY,
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


EXPO_RE = re.compile(r"exposic|palmadotze", re.I)


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


def main() -> int:
    html = fetch_html(PAGE)
    nou = detectar_nou(html)
    if not nou:
        return 0  # silenci: cap mes nou
    print(f"NOU MES DETECTAT: {nou['label']} -> {nou['url']}")
    text = extreure_text_pdf(nou["url"])

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
    d["municipio"] = "Santa Margarida i els Monjos"
    d["mes"] = nou["label"]
    d["fuente_pdf"] = nou["url"]
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
        "pdf": nou["url"], "default": True,
        "fuente": "extraccio completa (LLM deepseek-v4-pro via gateway OpenClaw)",
    })
    ags["default"] = nou["id"]
    json.dump(ags, open(os.path.join(REPO, "data", "agendas.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # commit + push
    subprocess.run(["git", "-C", REPO, "add", "-A"], check=True)
    subprocess.run(["git", "-C", REPO, "-c", "user.name=hrodres",
                    "-c", "user.email=hrodres@users.noreply.github.com", "commit", "-q",
                    "-m", f"Agenda {nou['label']}: JSON generat (deepseek-v4-pro) + push automàtic"], check=True)
    subprocess.run(["git", "-C", REPO, "push", "origin", "main"], check=True)
    print(f"PROCESSAT i PUSHEJAT: {nou['label']} — {len(d['eventos'])} events, "
          f"{len(d.get('contactes', []))} contactes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
