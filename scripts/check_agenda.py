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
    # [Agenda <mes> <any>](<url .pdf>)
    pat = re.compile(r"\[Agenda\s+([A-Za-zçàèéíòóú·]+)\s+(\d{4})\]\((https://[^)]+\.pdf)\)", re.I)
    for m in pat.finditer(html):
        mes = m.group(1).lower()
        any_ = int(m.group(2))
        url = m.group(3)
        if mes not in MESES:
            continue
        key = any_ * 12 + MESES[mes]
        mid = f"{mes}-{any_}"
        label = f"{m.group(1).capitalize()} {any_}"
        out.append({"id": mid, "label": label, "url": url, "key": key})
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
     "precio_general":str|null,"descripcion":str,"enlace_maps":str "URL Google Maps search URL-encoded"}
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
- Si un element no encaixa en cap grup: subcategoria/subsubcategoria a null. MAI 'Altres'.
- 'enlace_maps': https://www.google.com/maps/search/?api=1&query=<lloc>+Santa+Margarida+i+els+Monjos (URL-encoded).
- Inclou TOTS els esdeveniments i els contactes de la pàgina de Telèfons d'interès.
- Només el JSON, res més."""


def generar_json(text: str, label: str) -> dict | None:
    prompt_path = "/tmp/agenda_prompt.txt"
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(PROMPT_SCHEMA + "\n\nAGENDA: " + label + "\n\nTEXT DEL PDF:\n" + text)
    try:
        r = subprocess.run(
            ["openclaw", "agent", "--model", MODEL, "--session-key", SESSION_KEY,
             "--message-file", prompt_path, "--json"],
            capture_output=True, text=True, timeout=600,
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


def aplicar_regles(d: dict) -> dict:
    for ev in d.get("eventos", []):
        if ev.get("seccio") == "Esports":
            ev["subsubcategoria"] = None
    return d


def main() -> int:
    html = fetch_html(PAGE)
    nou = detectar_nou(html)
    if not nou:
        return 0  # silenci: cap mes nou
    print(f"NOU MES DETECTAT: {nou['label']} -> {nou['url']}")
    text = extreure_text_pdf(nou["url"])
    d = generar_json(text, nou["label"])
    if not d or len(d.get("eventos", [])) < MIN_EVENTS:
        print(f"Resultat insuficient ({len(d.get('eventos',[])) if d else 0} events); no es toca res.")
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
