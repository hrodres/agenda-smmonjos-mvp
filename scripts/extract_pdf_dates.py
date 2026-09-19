#!/usr/bin/env python3
"""
Extractor heuristic de l'agenda municipal (format juliol-agost: per dates).
No es fa servir LLM: parseja el text del PDF amb regles.
- Events fechats: sota capcaleres DIUMENGE/DIMECRES...+dia+mes.
- Cursos/serveis: blocs de FORMACIO/ESPORT/NOTICIES sense data concreta.
NO usa mai 'Altres' com a agrupacio.
Usage: python3 extract_pdf_dates.py <pdf> <mes_label> <sortida.json>
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from urllib.parse import quote

import pdfplumber

MESES = {
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12,
}
DIES = r"(diumenge|dilluns|dimarts|dimecres|dijous|divendres|dissabte)"
DATE_HDR = re.compile(rf"^{DIES}\s+(\d{{1,2}})\s*$", re.I)
MONTH_LINE = re.compile(rf"^({'|'.join(MESES.keys())})\s*$", re.I)
TIME = re.compile(r"(\d{1,2})[.:](\d{2})\s*h", re.I)
ANY_DEF = 2026


def parse_time(txt):
    m = TIME.search(txt)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def maps_url(lloc):
    if not lloc:
        return None
    q = lloc + ", Santa Margarida i els Monjos"
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def categoria_per_text(txt):
    t = txt.lower()
    if any(k in t for k in ["teatre", "obra"]):
        return "Teatre"
    if any(k in t for k in ["concert", "cantada", "havaneres", "sardanes", "ball", "orquestra", "dj ", "musical"]):
        return "Música"
    if any(k in t for k in ["infantil", "nens", "criatures", "bombeta", "pisicina", "campus", "escola"]):
        return "Infantil"
    if any(k in t for k in ["festa major", "foguera", "correfoc", "diables", "traca", "cercavila", "goigs", "sardanes", "ofici"]):
        return "Festes"
    if any(k in t for k in ["esport", "cursa", "campus", "vòlei", "hoquei", "bàsquet", "futbol", "patinatge", "ping pong", "zumba", "gimnàs", "caminada", "marx"]):
        return "Esport"
    if any(k in t for k in ["curs", "taller", "formació", "escola d'adults", "ocupació", "idiomes", "informàtica"]):
        return "Formació"
    if any(k in t for k in ["exposició", "mostra", "galeria", "memòria", "cultura"]):
        return "Cultura"
    if any(k in t for k in ["mercat", "sopar", "esmorzar", "dinar", "degustació", "coc", "cava", "vermut", "bento", "bingo"]):
        return "Gastronomia"
    return "Altres"


def seccio_de_bloc(header):
    h = header.lower()
    if "formació" in h or "ocupació" in h or "escola" in h or "curs" in h:
        return "Formació"
    if "esport" in h or "campus" in h:
        return "Esports"
    if "notícies" in h:
        return "Notícies"
    return "Actes"


def main():
    pdf_path, mes_label, out = sys.argv[1], sys.argv[2], sys.argv[3]
    eventos = []
    contactes = []
    page_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            page_texts.append(p.extract_text() or "")

    n = 0

    def add(titulo, fecha, hora, lloc, descripcio, seccio, sub=None, subsub=None):
        nonlocal n
        n += 1
        cat = categoria_per_text(titulo + " " + descripcio)
        eventos.append({
            "id": f"evt-{mes_label.lower().replace(' ', '-')}-{n:03d}",
            "titulo": titulo.strip(),
            "fecha_inicio": fecha,
            "fecha_fin": fecha,
            "hora_inicio": hora,
            "hora_fin": None,
            "lugar": lloc,
            "categoria": cat,
            "seccio": seccio,
            "subcategoria": sub,
            "subsubcategoria": subsub,
            "precio_socios": None,
            "precio_general": None,
            "descripcion": descripcio.strip(),
            "enlace_maps": maps_url(lloc),
            "fuente": "PDF (extraccio heurística)",
        })

    # PAGINES 2-9: calendar per dates
    mes_actual = None
    for txt in page_texts[1:9]:
        lines = [l.rstrip() for l in txt.split("\n") if l.strip()]
        i = 0
        while i < len(lines):
            mm = MONTH_LINE.match(lines[i])
            if mm:
                mes_actual = MESES[mm.group(1).lower()]
                i += 1
                continue
            m = DATE_HDR.match(lines[i])
            if m and mes_actual:
                dia = int(m.group(2))
                # titol: les seguents linies en majuscules/noms propis fins al primer
                # blanc de descripcio (l'hora o "A les")
                j = i + 1
                titol_parts = []
                while j < len(lines):
                    ln = lines[j]
                    if DATE_HDR.match(ln) or MONTH_LINE.match(ln):
                        break
                    if re.match(r"^(A les|De \d|Imprescindible|Organitza|Cal |Inscripció|Dissabte|Diumenge|Dilluns|Dimarts|Dimecres|Dijous|Divendres)", ln):
                        break
                    if ln.isupper() or re.match(r"^[A-ZÀ-Ý]", ln):
                        titol_parts.append(ln)
                        j += 1
                    else:
                        break
                titol = " ".join(titol_parts).strip() or "(activitat)"
                # descripcio: des de j fins al seguent DATE_HDR / MONTH / fi
                desc_parts = []
                while j < len(lines) and not DATE_HDR.match(lines[j]) and not MONTH_LINE.match(lines[j]):
                    desc_parts.append(lines[j])
                    j += 1
                descripcio = " ".join(desc_parts)
                hora = parse_time(descripcio)
                lloc = None
                lm = re.search(r"(a[l]?\s+(?:la\s+|l'|el\s+)?([A-ZÀ-Ý][\wÀ-Ý\s'·]+?)(?:\.|,|\s+i\s|\s+A les|\s+De |\s+Imprescindible|\s+Organitza|\s+Cal |\s+Inscripció|$))", descripcio)
                if lm:
                    lloc = lm.group(2).strip(" .,")
                seccio = "Actes"
                if any(k in (titol + descripcio).lower() for k in ["campus", "curs", "escola d'adults", "ocupació"]):
                    seccio = "Formació"
                elif any(k in (titol + descripcio).lower() for k in ["vòlei", "hoquei", "bàsquet", "futbol", "patinatge", "piscina"]):
                    seccio = "Esports"
                fecha = f"{ANY_DEF}-{mes_actual:02d}-{dia:02d}"
                add(titol, fecha, hora, lloc, descripcio, seccio)
                i = j
            else:
                i += 1

    # PAGINES 10-12: blocs seccio (formacio/esport/noticies)
    for txt in page_texts[9:12]:
        # cerca capcaleres de seccio
        for kw in ["FORMACIÓ I CURSOS", "SERVEI LOCAL", "ESPORT", "NOTÍCIES", "Escola Municipal de Formació"]:
            idx = txt.find(kw)
            if idx >= 0:
                block = txt[idx:idx + 2000]
                seccio = seccio_de_bloc(kw)
                # noms de curs/campus + rang de dates proper
                nom_pat = re.compile(r"(Campus\s+d[e']?\s*[\wÀ-Ý]+|Cursos?\s+d[e']?\s*[\wÀ-Ý]+|CURS\s+[\wÀ-Ý]+)", re.I)
                rang_pat = re.compile(
                    r"(?:Del|De)\s+(\d{1,2})\s+de\s+(\w+)\s+(?:al|i\s+el)\s+(\d{1,2})\s+de\s+(\w+)"
                    r"|Fins\s+(?:al|el)\s+(\d{1,2})\s+de\s+(\w+)", re.I)
                for nm in nom_pat.finditer(block):
                    nom = nm.group(1).strip(" .,")
                    rest = block[nm.end():nm.end() + 400]
                    rm = rang_pat.search(rest)
                    if not rm:
                        continue
                    if rm.group(1):
                        d1, mes1 = int(rm.group(1)), MESES.get(rm.group(2).lower())
                        d2, mes2 = int(rm.group(3)), MESES.get(rm.group(4).lower())
                    else:
                        d1 = d2 = int(rm.group(5)); mes1 = mes2 = MESES.get(rm.group(6).lower())
                    if mes1 and mes2:
                        add(nom, f"{ANY_DEF}-{mes1:02d}-{d1:02d}", None, None,
                            "Activitat de " + kw.lower() + ". " + rm.group(0).strip(),
                            seccio, sub="Cursos i Activitats" if seccio == "Formació" else None)

    payload = {
        "municipio": "Santa Margarida i els Monjos",
        "mes": mes_label,
        "fuente_pdf": pdf_path,
        "generado": date.today().isoformat(),
        "generado_por": "extract_pdf_dates (heuristic)",
        "total": len(eventos),
        "eventos": eventos,
        "contactes": contactes,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Generats {len(eventos)} events -> {out}")


if __name__ == "__main__":
    main()
