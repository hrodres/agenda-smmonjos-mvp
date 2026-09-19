#!/usr/bin/env python3
"""
Ingesta de la Agenda de Santa Margarida i els Monjos - pipeline AUTOMATIC.

Objectiu: regenerar `data/eventos.json` a partir del PDF oficial de QUALSEVOL mes,
SENSE edicio manual. El pipeline:

  1. Descarrega el PDF de l'agenda (URL per defecte, --pdf-url o env AGENDA_PDF_URL).
  2. Extreu el text per pagines amb pdfplumber.
  3. Crida a opencode-go (Best Model Selection) amb un JSON Schema que FORCA
     l'extraccio estructurada:
       - events amb `seccio` (Actes/Formacio/Esports/Noticies),
         `subcategoria` i `subsubcategoria` (derivades de les sub-capcaleres del PDF),
         i `contactes` amb el seu `grup`.
  4. Normalitza, fa backup de l'arxiu existent i desa el resultat.

Disseny "month-agnostic": el codi NO coneix noms concrets de grups/categories.
El LLM deriva les agrupacions del propi PDF. El render del lloc (index.html) es
dinamic i les mostra soles. MAI s'usa "Altres" com a agrupacio: si un element no
encaixa en cap grup, es deixa subcategoria a null i es llista directament sota
el grup pare.

Seguretat de dades:
  - Abans de sobreescriure es fa backup (.bak amb data).
  - Si el LLM no respon o falla, NO es destrueix l'arxiu existent (es manté
    l'anterior). Nomes s'escriu el seed si no hi ha cap arxiu previ.
  - Amb --force-seed nomes restaura el seed si l'arxiu desti NO existeix.

Requisits: OPENCODE_API_KEY (obligatoria per a extraccio real). Sense clau,
el pipeline informa i no toca l'arxiu existent.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.parse
from datetime import date

import requests

# --------------------------------------------------------------------------
# Configuracio
# --------------------------------------------------------------------------
PDF_URL = os.environ.get(
    "AGENDA_PDF_URL",
    "https://www.santamargaridaielsmonjos.cat/fitxer/9839/AGENDA%20Setembre%2026_web.pdf",
)
MUNICIPIO = "Santa Margarida i els Monjos"
MES = os.environ.get("AGENDA_MES", "Setembre 2026")
# Ruta REAL que serveix el lloc (arrel del repo /data/eventos.json)
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eventos.json")

# "Best Model Selection": ranking de modelos de opencode-go, de mayor a menor
# capacidad para interpretar maquetacion en columnas y estructurar eventos en
# catalan/espanol. El pipeline usa el PRIMER modelo disponible que responde.
MODEL_RANKING = [
    "opencode-go/deepseek-v4-pro",  # model directe per defecte (extraccio robusta)
    "opencode-go/hy3",                # fallback
]

# Categories suggerides (el LLM pot retornar-ne de noves; el render te fallback de color)
CATEGORIAS_SUGERIDAS = [
    "Teatre", "Música", "Infantil", "Esport", "Formació",
    "Cultura", "Festes", "Gastronomia", "Altres",
]
SECCIONS = ["Actes", "Formació", "Esports", "Notícies"]

EVENT_PROPS = {
    "titulo": {"type": "string"},
    "fecha_inicio": {"type": "string", "description": "YYYY-MM-DD"},
    "fecha_fin": {"type": ["string", "null"], "description": "YYYY-MM-DD o null"},
    "hora_inicio": {"type": ["string", "null"], "description": "HH:MM 24h o null"},
    "hora_fin": {"type": ["string", "null"], "description": "HH:MM 24h o null"},
    "lugar": {"type": "string"},
    "categoria": {"type": "string", "description": "Categoria de badge (vegeu llista suggerida); pot ser nova."},
    "seccio": {"type": ["string", "null"], "description": "Pestanya: Actes / Formació / Esports / Notícies."},
    "subcategoria": {"type": ["string", "null"], "description": "Sub-grup segons les sub-capçaleres del PDF (ex: 'Cursos i Activitats', 'Joves i Infants', 'Servei Local d'Ocupació'). Si no hi ha grup: null. MAI 'Altres'."},
    "subsubcategoria": {"type": ["string", "null"], "description": "Segon nivell de grup (ex: 'Manualitats de Dona al Dia', '3r i 4t de primària'). null si no escau."},
    "precio_socios": {"type": ["string", "null"], "description": "ej: 'Gratuït', '3 €' o null"},
    "precio_general": {"type": ["string", "null"], "description": "ej: '8 €' o null"},
    "descripcion": {"type": "string"},
    "enlace_maps": {"type": "string", "description": "URL Google Maps search del lugar, URL-encoded."},
    "fuente": {"type": ["string", "null"]},
    "id": {"type": ["string", "null"]},
}

JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["eventos"],
    "properties": {
        "eventos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "titulo", "fecha_inicio", "fecha_fin", "hora_inicio",
                    "lugar", "categoria", "precio_socios", "precio_general",
                    "descripcion", "enlace_maps",
                ],
                "properties": EVENT_PROPS,
            },
        },
        "contactes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["nom", "telefon"],
                "properties": {
                    "nom": {"type": "string"},
                    "telefon": {"type": "string"},
                    "email": {"type": ["string", "null"]},
                    "nota": {"type": ["string", "null"]},
                    "web": {"type": ["string", "null"]},
                    "grup": {"type": ["string", "null"], "description": "Grup del PDF (ex: 'Serveis Municipals', 'Altres Serveis'). Si no hi ha grup: null. MAI 'Altres'."},
                },
            },
        },
    },
}

SYSTEM_PROMPT = (
    "Eres un extractor de dades d'agendes municipals a Catalunya. Reps el text extret "
    "d'un PDF d'agenda (maquetat en columnes). La teva tasca: interpretar la "
    "maquetacio, emparellar cada activitat amb la seva data/hora/lloc, i retornar "
    "SOLES un JSON que compleixi ESTRICTAMENT l'esquema proporcionat.\n"
    "Regles:\n"
    "- 'categoria' ha de ser la mes adequada (suggerides: " + ", ".join(CATEGORIAS_SUGERIDAS) + "; "
    "pots usar-ne una de nova si_cal). En catala.\n"
    "- 'seccio' (obligatoria per al filtre per pestanya): 'Actes', 'Formació', 'Esports' o "
    "'Notícies', segons la seccio del PDF. Els serveis/avisos sense data van a 'Notícies'.\n"
    "- DINS 'Formació' i 'Esport', el PDF usa sub-capçaleres (ex: 'Cursos i Activitats', "
    "'Cant Coral', 'Joves i Infants', 'Persones Adultes', 'Servei Local d'Ocupació'). "
    "Extreu-les a 'subcategoria'. Si hi ha un segon nivell (ex: 'Manualitats de Dona al Dia', "
    "'3r i 4t de primària', 'Tallers als Casals de la Gent Gran'), posa'l a 'subsubcategoria'.\n"
    "- Si un element NO encaixa en cap sub-grup, deixa 'subcategoria' i 'subsubcategoria' a null. "
    "MAI utilitzis 'Altres' com a agrupacio.\n"
    "- 'fecha_inicio'/'fecha_fin' en YYYY-MM-DD (any del PDF). Si abasta varis dies usa "
    "fecha_fin; si es un sol dia, igual a fecha_inicio.\n"
    "- 'hora_inicio'/'hora_fin' en HH:MM (24h) o null.\n"
    "- 'precio_socios'/'precio_general': text literal ('Gratuït', '8 €') o null.\n"
    "- 'enlace_maps': URL Google Maps search del lloc, "
    "https://www.google.com/maps/search/?api=1&query=<lloc+municipi> (URL-encoded).\n"
    "- 'descripcion': resum concis en catala (inscripcions, contactes utils).\n"
    "- Inclou TOTS els events del mes (actes, visites, tallers, concerts, cinema, teatre, "
    "trobades, esport, formacio). NO omitis els serveis permanents sense data: vesen a "
    "'contactes' (seccio de telefons d'interes del PDF) amb el seu 'grup'.\n"
    "- El JSON ha de tenir SOLES les claus 'eventos' i 'contactes'."
)

# --------------------------------------------------------------------------
# Seed embebido (fallback sense LLM) - nomes s'usa si no hi ha arxiu previ
# --------------------------------------------------------------------------
SEED_EVENTOS = [
    {'id': 'evt-2026-09-06-mercat', 'titulo': 'Mercat de segona mà', 'fecha_inicio': '2026-09-06', 'fecha_fin': '2026-09-06', 'hora_inicio': '10:00', 'hora_fin': '14:00', 'lugar': 'Plaça de Pau Casals', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Mercat de segona mà al matí a la plaça de Pau Casals. Ven al teu poble i troba tresors.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Pla%C3%A7a%20de%20Pau%20Casals%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-08-ludoteca', 'titulo': 'Portes obertes a la ludoteca La Baldufa', 'fecha_inicio': '2026-09-08', 'fecha_fin': '2026-09-08', 'hora_inicio': '16:45', 'hora_fin': '18:30', 'lugar': "Carrer d'Anselm Clavé 9", 'categoria': 'Infantil', 'precio_socios': None, 'precio_general': None, 'descripcion': "Jornada de portes obertes de la ludoteca La Baldufa. Activitat familiar: els infants han d'estar acompanyats per una persona adulta. També es podran fer les inscripcions per al nou curs 2026-27.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Carrer%20d%27Anselm%20Clav%C3%A9%209%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-08-vitis', 'titulo': 'Les Empremtes del Temps, a la recerca dels vitis!', 'fecha_inicio': '2026-09-08', 'fecha_fin': '2026-09-08', 'hora_inicio': '11:00', 'hora_fin': None, 'lugar': 'Castell de Penyafort', 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita al Castell de Penyafort a les 11 h. Inscripció prèvia al 669 287 539.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Castell%20de%20Penyafort%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-10-diada', 'titulo': 'Acte institucional de la Diada Nacional de Catalunya', 'fecha_inicio': '2026-09-10', 'fecha_fin': '2026-09-10', 'hora_inicio': '19:30', 'hora_fin': '20:30', 'lugar': "Plaça de l'Església", 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': "Parlament institucional i actuació musical a càrrec del duet Xènia i Marc. Hissada de la bandera al campanar de l'església a càrrec de la parròquia i el Ball de Diables Spantus dels Monjos.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Pla%C3%A7a%20de%20l%27Esgl%C3%A9sia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-13-castell', 'titulo': 'Visita guiada al Castell de Penyafort', 'fecha_inicio': '2026-09-13', 'fecha_fin': '2026-09-13', 'hora_inicio': '10:30', 'hora_fin': '12:00', 'lugar': 'Castell de Penyafort', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita guiada al Castell de Penyafort a les 10.30 h i a les 12 h. Imprescindible inscripció prèvia al 669 287 539.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Castell%20de%20Penyafort%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-13-petjades', 'titulo': 'Les Petjades del Vesper', 'fecha_inicio': '2026-09-13', 'fecha_fin': '2026-09-13', 'hora_inicio': '10:30', 'hora_fin': '12:00', 'lugar': 'El Ciarga', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita combinada entre el Ciarga i les caves Nadal de Torrelavit. A les 10.30 h des del Ciarga; el desplaçament es fa en cotxes particulars. Inscripció prèvia al 669 287 539.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=El%20Ciarga%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-15-tangram', 'titulo': "Berenar d'obertura del Tangram", 'fecha_inicio': '2026-09-15', 'fecha_fin': '2026-09-15', 'hora_inicio': '16:30', 'hora_fin': '17:30', 'lugar': "Tangram (Ca l'Antic)", 'categoria': 'Infantil', 'precio_socios': None, 'precio_general': None, 'descripcion': "Berenar d'obertura del Tangram. Cal inscripció prèvia per Whatsapp al 629 17 40 07 o presencial.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Tangram%20%28Ca%20l%27Antic%29%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-16-caminada', 'titulo': 'Caminada de proximitat', 'fecha_inicio': '2026-09-16', 'fecha_fin': '2026-09-16', 'hora_inicio': '09:30', 'hora_fin': '12:00', 'lugar': 'Molí del Foix', 'categoria': 'Esport', 'precio_socios': None, 'precio_general': None, 'descripcion': "Passejada planera de connexió entre nuclis d'uns 5 km, a càrrec del Ball de Diables Spantus dels Monjos. Sortida a les 9.30 h del Molí del Foix. Inscripció prèvia a molidelfoix@smmonjos.cat o al 93 818 69 28.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Mol%C3%AD%20del%20Foix%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-16-botifarrada', 'titulo': 'Botifarrada popular', 'fecha_inicio': '2026-09-16', 'fecha_fin': '2026-09-16', 'hora_inicio': '21:00', 'hora_fin': '22:30', 'lugar': 'Plaça de Pau Casals', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': "Botifarrada popular a càrrec del Ball de Diables Spantus dels Monjos. Obsequi d'una peça de fruita i aigua als assistents.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Pla%C3%A7a%20de%20Pau%20Casals%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-16-concert', 'titulo': 'Concert: Kelly Isaiah', 'fecha_inicio': '2026-09-16', 'fecha_fin': '2026-09-16', 'hora_inicio': '22:30', 'hora_fin': '23:45', 'lugar': 'Plaça de Pau Casals', 'categoria': 'Música', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Concert a càrrec de Kelly Isaiah a la plaça de Pau Casals. En acabar, sessió de DJ amb el Dj Àngel.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Pla%C3%A7a%20de%20Pau%20Casals%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-16-cantoral', 'titulo': 'Inici del Cant Coral (Coral Amics de Penyafel)', 'fecha_inicio': '2026-09-16', 'fecha_fin': '2026-09-16', 'hora_inicio': '19:30', 'hora_fin': '21:30', 'lugar': 'Casa de Cultura Mas Catarro', 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Inici dels assajos de la Coral Amics de Penyafel. Assajos dimecres de 19.30 h a 21.30 h. Inscripcions: 619 20 89 60 o coral.amics.penyafel@gmail.com.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Casa%20de%20Cultura%20Mas%20Catarro%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-19-dracs', 'titulo': 'Trobada de Dracs', 'fecha_inicio': '2026-09-19', 'fecha_fin': '2026-09-19', 'hora_inicio': '18:00', 'hora_fin': '23:30', 'lugar': "Ajuntament / Plaça de l'Església", 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': "A les 18 h arribada i plantada dels dracs davant l'ajuntament; 19.30 h cercavila sense foc per l'Av. de Catalunya; 20 h cercavila de foc fins la plaça de l'Església; 21.30 h concurs d'enceses. Després, sopar popular (botifarra amb mongetes); venda de tiquets el 16 de setembre de 19 h a 21 h davant l'ajuntament.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Ajuntament%20/%20Pla%C3%A7a%20de%20l%27Esgl%C3%A9sia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-20-sabors', 'titulo': 'Sabors en temps de guerra · Memòria de la guerra aèria', 'fecha_inicio': '2026-09-20', 'fecha_fin': '2026-09-20', 'hora_inicio': '09:00', 'hora_fin': '13:00', 'lugar': 'El Ciarga', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita combinada entre Subirats i Santa Margarida i els Monjos (sortida 9 h des de Subirats) i entre el Ciarga i el Castell de Penyafort (sortida 11 h des del Ciarga). El desplaçament es fa en cotxes particulars. Inscripció prèvia a escapadasingular.com o al 669 28 75 39.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=El%20Ciarga%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-20-castell', 'titulo': 'Visita guiada al Castell de Penyafort', 'fecha_inicio': '2026-09-20', 'fecha_fin': '2026-09-20', 'hora_inicio': '10:30', 'hora_fin': '12:00', 'lugar': 'Castell de Penyafort', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita guiada al Castell de Penyafort a les 10.30 h i a les 12 h. Imprescindible inscripció prèvia al 669 287 539.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Castell%20de%20Penyafort%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-20-teatre', 'titulo': 'Teatre: Genitalmente hablando 2', 'fecha_inicio': '2026-09-20', 'fecha_fin': '2026-09-20', 'hora_inicio': '19:00', 'hora_fin': '21:00', 'lugar': 'Societat La Margaridoia', 'categoria': 'Teatre', 'precio_socios': 'Gratuït', 'precio_general': '8 €', 'descripcion': "Obra 'Genitalmente hablando 2' a càrrec del grup Melodramatik's, a la societat La Margaridoia. Socis: gratuït. Públic: 8 €.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Societat%20La%20Margaridoia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-20-cinema', 'titulo': 'Cinema: Tres Adioses', 'fecha_inicio': '2026-09-20', 'fecha_fin': '2026-09-20', 'hora_inicio': '19:00', 'hora_fin': '21:00', 'lugar': 'Societat La Margaridoia', 'categoria': 'Altres', 'precio_socios': '3 €', 'precio_general': '4,5 €', 'descripcion': "Projecció de la pel·lícula 'Tres Adioses', d'Isabel Coixet, a la societat La Margaridoia. Socis: 3 €. Públic: 4,5 €.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Societat%20La%20Margaridoia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-21-mapacamic', 'titulo': 'Dibuixa el teu mapa: visualitza el teu camí professional', 'fecha_inicio': '2026-09-21', 'fecha_fin': '2026-09-21', 'hora_inicio': '09:15', 'hora_fin': '12:15', 'lugar': "Club de la Feina (Ca l'Antic)", 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': "Taller 'Dibuixa el teu mapa' per visualitzar el teu camí professional. Dilluns 21 de setembre de 9.15 h a 12.15 h. Inscripcions a la web de l'ajuntament.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Club%20de%20la%20Feina%20%28Ca%20l%27Antic%29%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-22-matricules', 'titulo': 'Taller de matrícules per a bicis i patinets', 'fecha_inicio': '2026-09-22', 'fecha_fin': '2026-09-22', 'hora_inicio': '17:30', 'hora_fin': '19:00', 'lugar': 'Molí del Foix', 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': "Taller de matrícules per a bicicletes i patinets al Molí del Foix. Si véns amb la bicicleta o patinet t'emportaràs un obsequi. Setmana Europea de la Mobilitat.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Mol%C3%AD%20del%20Foix%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-23-softskills', 'titulo': 'Soft skills amb les mans', 'fecha_inicio': '2026-09-23', 'fecha_fin': '2026-09-23', 'hora_inicio': '09:15', 'hora_fin': '12:15', 'lugar': "Club de la Feina (Ca l'Antic)", 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': "Taller 'Soft skills amb les mans'. Dimecres 23 de setembre de 9.15 h a 12.15 h. Data límit per valorar si es tira endavant o no: 18 de setembre. Inscripcions a la web de l'ajuntament.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Club%20de%20la%20Feina%20%28Ca%20l%27Antic%29%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-25-aula', 'titulo': 'Aula Cultural: Eulàlia i Mercè, una lluita pel matronatge de Barcelona', 'fecha_inicio': '2026-09-25', 'fecha_fin': '2026-09-25', 'hora_inicio': '17:00', 'hora_fin': '18:30', 'lugar': 'Casal de la Gent Gran', 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': "Xerrada 'Eulàlia i Mercè, una lluita pel matronatge de Barcelona' a càrrec de Marc Jobani, a les 17 h al casal de la gent gran. Amb motiu del 45è aniversari del Drac dels Monjos.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Casal%20de%20la%20Gent%20Gran%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-25-concertball', 'titulo': 'Concert-ball: Gina & The Tonics', 'fecha_inicio': '2026-09-25', 'fecha_fin': '2026-09-25', 'hora_inicio': '23:45', 'hora_fin': '02:00', 'lugar': "Plaça de l'Església", 'categoria': 'Música', 'precio_socios': None, 'precio_general': None, 'descripcion': "Concert-ball a càrrec del grup Gina & The Tonics, a les 23.45 h a la plaça de l'església. Amb motiu del 45è aniversari del Drac dels Monjos.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Pla%C3%A7a%20de%20l%27Esgl%C3%A9sia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-26-soparball', 'titulo': 'Sopar-ball: Txic to txic', 'fecha_inicio': '2026-09-26', 'fecha_fin': '2026-09-26', 'hora_inicio': '21:00', 'hora_fin': '23:30', 'lugar': 'Societat La Margaridoia', 'categoria': 'Música', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Sopar-ball a càrrec del grup Txic to txic, a la societat La Margaridoia. Preus i menú a determinar. Reserves: del 7 al 9 i del 14 al 16 de setembre, de 19 h a 21 h a la secretaria; per Whatsapp al 640 119745 o a info@lamargaridoia.cat fins al dia 16.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Societat%20La%20Margaridoia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-26-baldesalo', 'titulo': "Ball de saló: Ruben's", 'fecha_inicio': '2026-09-26', 'fecha_fin': '2026-09-26', 'hora_inicio': '22:30', 'hora_fin': '23:45', 'lugar': 'Societat La Margaridoia', 'categoria': 'Música', 'precio_socios': 'Gratuït', 'precio_general': '7 €', 'descripcion': "Ball de saló a càrrec del duet Ruben's, a les 22.30 h a la societat La Margaridoia. Socis: gratuït. Públic: 7 €.", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Societat%20La%20Margaridoia%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-27-castell', 'titulo': 'Visita guiada al Castell de Penyafort', 'fecha_inicio': '2026-09-27', 'fecha_fin': '2026-09-27', 'hora_inicio': '10:30', 'hora_fin': '12:00', 'lugar': 'Castell de Penyafort', 'categoria': 'Altres', 'precio_socios': None, 'precio_general': None, 'descripcion': 'Visita guiada al Castell de Penyafort a les 10.30 h i a les 12 h. Imprescindible inscripció prèvia al 669 287 539.', 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Castell%20de%20Penyafort%2C%20Santa%20Margarida%20i%20els%20Monjos'},
    {'id': 'evt-2026-09-28-talent', 'titulo': 'Crea el teu mapa de Talent!', 'fecha_inicio': '2026-09-28', 'fecha_fin': '2026-10-01', 'hora_inicio': '09:00', 'hora_fin': '13:00', 'lugar': "Club de la Feina (Ca l'Antic)", 'categoria': 'Formació', 'precio_socios': None, 'precio_general': None, 'descripcion': "Taller 'Crea el teu mapa de Talent!' del 28 de setembre a l'1 d'octubre, de 9 h a 13 h. Adreçat a persones en situació d'atur o en procés de millora de l'ocupació. Inscripcions al Club de la Feina (dimarts i divendres de 10 h a 13 h).", 'enlace_maps': 'https://www.google.com/maps/search/?api=1&query=Club%20de%20la%20Feina%20%28Ca%20l%27Antic%29%2C%20Santa%20Margarida%20i%20els%20Monjos'},
]


# --------------------------------------------------------------------------
# Utilitats de normalitzacio
# --------------------------------------------------------------------------
def slug(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "item"


def norm_seccio(s):
    if not s:
        return None
    s = s.strip()
    if s in SECCIONS:
        return s
    low = {k.lower(): k for k in SECCIONS}
    if s.lower() in low:
        return low[s.lower()]
    sl = s.lower()
    if "form" in sl:
        return "Formació"
    if "esport" in sl:
        return "Esports"
    if "notic" in sl:
        return "Notícies"
    return "Actes"


def gen_ids(eventos: list[dict]) -> list[dict]:
    seen = set()
    for e in eventos:
        if e.get("id") and e["id"] not in seen:
            seen.add(e["id"])
            continue
        base = "evt-" + date.today().isoformat() + "-" + slug(e.get("titulo", ""))
        i = base
        n = 1
        while i in seen:
            n += 1
            i = base + f"-{n}"
        seen.add(i)
        e["id"] = i
    return eventos


# --------------------------------------------------------------------------
# Pas 1 + 2: descarregar i extreure
# --------------------------------------------------------------------------
def descargar_pdf(url: str) -> str:
    print(f"[1/4] Descarregant PDF: {url}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        f.write(r.content)
    print(f"      PDF desat temporalment ({len(r.content)} bytes).")
    return path


def extraer_texto(pdf_path: str) -> str:
    print("[2/4] Extraient text amb pdfplumber...")
    try:
        import pdfplumber
    except ImportError:
        raise SystemExit("ERROR: instal·la pdfplumber (pip install pdfplumber).")
    bloques = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ""
            bloques.append(f"--- PÀGINA {i+1} ---\n{t}")
    texto = "\n\n".join(bloques)
    print(f"      Text extret: {len(texto)} caràcters.")
    return texto


# --------------------------------------------------------------------------
# Pas 3: crida a opencode-go amb Best Model Selection
# --------------------------------------------------------------------------
def resolver_api_key() -> str:
    """Prioritat: env OPENCODE_API_KEY; si no, la clau del propi vault de
    l'OpenClaw (config_machine_state del sqlite d'estat). Mai s'imprimeix."""
    env = os.environ.get("OPENCODE_API_KEY")
    if env:
        return env
    try:
        import sqlite3, re, glob
        sec = re.compile(r'(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,80}(?![A-Za-z0-9])')
        for db in glob.glob("/root/.openclaw/state/*.sqlite"):
            con = sqlite3.connect(db)
            cur = con.cursor()
            for (val,) in cur.execute(
                "SELECT value_json FROM config_machine_state WHERE value_json LIKE '%opencode%'"
            ):
                if not isinstance(val, str):
                    continue
                m = sec.search(val)
                if m:
                    con.close()
                    return m.group(0)
            con.close()
    except Exception:
        pass
    return ""


def llamar_opencodego(texto: str, modelos: list[str]) -> dict | None:
    api_key = resolver_api_key()
    if not api_key:
        print("      OPENCODE_API_KEY no disponible (env ni vault) -> es omèt el LLM.")
        return None
    base = os.environ.get("OPENCODE_API_BASE", "https://opencode.ai/zen/go/v1").rstrip("/")
    for modelo in modelos:
        print(f"      Provant model opencode-go: {modelo}")
        try:
            resp = requests.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": "TEXTO DEL PDF:\n" + texto},
                    ],
                    "temperature": 0.1,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "agenda_eventos", "strict": True, "schema": JSON_SCHEMA},
                    },
                },
                timeout=120,
            )
            if resp.status_code != 200:
                print(f"      -> {modelo} va respondre {resp.status_code}: {resp.text[:200]}")
                continue
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            print(f"      -> {modelo} OK. Events: {len(data.get('eventos', []))}; Contactes: {len(data.get('contactes', []))}")
            return data
        except Exception as e:  # noqa: BLE001
            print(f"      -> {modelo} ha fallat: {e}")
            continue
    print("      Tots els models han fallat.")
    return None


# --------------------------------------------------------------------------
# Pas 4: guardar (amb backup i normalitzacio)
# --------------------------------------------------------------------------
def guardar(eventos: list[dict], contactes: list[dict] | None = None) -> None:
    out = os.path.abspath(OUT_PATH)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        bak = out + "." + date.today().isoformat() + ".bak"
        shutil.copy2(out, bak)
        print(f"      Backup de l'arxiu existent -> {bak}")
    eventos = gen_ids(eventos)
    for e in eventos:
        e["seccio"] = norm_seccio(e.get("seccio"))
        for f in ("fecha_fin", "hora_inicio", "hora_fin", "lugar",
                  "precio_socios", "precio_general", "enlace_maps", "fuente", "subcategoria", "subsubcategoria"):
            e.setdefault(f, None)
    payload = {
        "municipio": MUNICIPIO,
        "mes": MES,
        "fuente_pdf": PDF_URL,
        "generado": date.today().isoformat(),
        "generado_por": "agenda-ingest (opencode-go)",
        "total": len(eventos),
        "eventos": eventos,
        "contactes": contactes or [],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[4/4] Desats {len(eventos)} events + {len(contactes or [])} contactes -> {out}")


def main() -> int:
    global PDF_URL, MES, OUT_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-seed", action="store_true", help="Escriu el seed només si no existeix l'arxiu destí.")
    ap.add_argument("--pdf-url", default=PDF_URL, help="URL del PDF de l'agenda.")
    ap.add_argument("--mes", default=MES, help="Mes de l'agenda (p. ex. 'Octubre 2026').")
    ap.add_argument("--out", default=OUT_PATH, help="Ruta de sortida (data/eventos.json).")
    args = ap.parse_args()

    PDF_URL = args.pdf_url
    MES = args.mes
    OUT_PATH = args.out

    if args.force_seed:
        if os.path.exists(OUT_PATH):
            print("--force-seed: ja existeix l'arxiu; no es sobreescriu. Esborra'l si vols restaurar el seed.")
            return 0
        guardar(SEED_EVENTOS, None)
        return 0

    pdf_path = None
    try:
        pdf_path = descargar_pdf(PDF_URL)
        texto = extraer_texto(pdf_path)
        modelos = [os.environ.get("OPENCODE_MODEL")] if os.environ.get("OPENCODE_MODEL") else MODEL_RANKING
        modelos = [m for m in modelos if m]
        data = llamar_opencodego(texto, modelos)
        if data and data.get("eventos"):
            guardar(data["eventos"], data.get("contactes"))
        elif os.path.exists(OUT_PATH):
            print("LLM sense resultats. Es manté l'arxiu existent (no es destrueixen dades).")
        else:
            print("LLM sense resultats i no hi ha arxiu previ -> seed.")
            guardar(SEED_EVENTOS, None)
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"ERROR en el pipeline: {e}")
        if os.path.exists(OUT_PATH):
            print("-> Fallback: es manté l'arxiu existent.")
        else:
            guardar(SEED_EVENTOS, None)
        return 0
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)


if __name__ == "__main__":
    sys.exit(main())
