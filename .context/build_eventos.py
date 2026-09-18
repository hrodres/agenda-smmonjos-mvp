import json, urllib.parse

def maps(lugar):
    q = urllib.parse.quote(f"{lugar}, Santa Margarida i els Monjos")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

ev = []
def add(id_, titulo, fecha_inicio, fecha_fin, hora_inicio, hora_fin, lugar, categoria, precio_socios, precio_general, descripcion):
    ev.append({
        "id": id_,
        "titulo": titulo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "lugar": lugar,
        "categoria": categoria,
        "precio_socios": precio_socios,
        "precio_general": precio_general,
        "descripcion": descripcion,
        "enlace_maps": maps(lugar),
    })

# ---- Actes destacats ----
add("evt-20260906-mercat", "Mercat de segona mà", "2026-09-06", None, "10:00", "14:00",
    "Plaça de Pau Casals", "Altres", None, None,
    "Mercat de segona mà a la plaça de Pau Casals.")
add("evt-20260908-portes-obertes-ludoteca", "Portes obertes a la Ludoteca La Baldufa", "2026-09-08", None, "16:45", "18:30",
    "Carrer d'Anselm Clavé 9", "Infantil", None, None,
    "Portes obertes a la Ludoteca La Baldufa. Els infants han d'anar acompanyats d'una persona adulta. També es podran fer les inscripcions per al nou curs.")
add("evt-20260908-les-petjades", "Les Petjades del Vesper", "2026-09-08", None, "10:30", None,
    "Ciarga", "Altres", None, None,
    "Visita combinada entre el Ciarga i les caves Nadal de Torrelavit. Sortida a les 10.30 h des del Ciarga. El desplaçament es fa en cotxes particulars. Inscripció prèvia al 669 287 539.")
add("evt-20260908-les-empremtes", "Les Empremtes del Temps, a la recerca dels vitis!", "2026-09-08", None, "11:00", None,
    "Castell de Penyafort", "Infantil", None, None,
    "Activitat familiar a la recerca dels vitis, al Castell de Penyafort. Inscripció prèvia al 669 287 539.")
add("evt-20260910-diada", "Acte institucional de commemoració de la Diada Nacional de Catalunya", "2026-09-10", None, "19:30", None,
    "Plaça de l'Església", "Música", None, None,
    "Parlament institucional i actuació musical a càrrec del duet Xènia i Marc. Hissada de la bandera al campanar de l'església a càrrec de la parròquia i el Ball de Diables Spantus dels Monjos. Es servirà una copa de cava.")
add("evt-20260910-botifarrada", "Botifarrada popular", "2026-09-10", None, "21:00", None,
    "Plaça de Pau Casals", "Altres", None, None,
    "Botifarrada popular a càrrec del Ball de Diables Spantus dels Monjos.")
add("evt-20260910-concert-diada", "Concert de Kelly Isaiah", "2026-09-10", None, "22:30", None,
    "Plaça de Pau Casals", "Música", None, None,
    "Concert a càrrec de Kelly Isaiah. En acabar, Dj Àngel.")
add("evt-20260913-visita-castell", "Visita guiada al Castell de Penyafort (turno 13/9)", "2026-09-13", None, "10:30", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. A les 10.30 h i a les 12 h. Imprescindible inscripció al 669 287 539.")
add("evt-20260913-visita-castell-2", "Visita guiada al Castell de Penyafort (12 h)", "2026-09-13", None, "12:00", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. Imprescindible inscripció al 669 287 539.")
add("evt-20260915-berenar-tangram", "Berenar d'obertura del Tangram", "2026-09-15", None, "16:30", None,
    "Tangram", "Infantil", None, None,
    "Berenar d'obertura del Tangram. Cal inscripció prèvia per Whatsapp al 629 174 007 o presencial.")
add("evt-20260916-caminada-proximitat", "Caminada de proximitat", "2026-09-16", None, "09:30", None,
    "Molí del Foix", "Esport", None, None,
    "Caminada de proximitat d'uns 5 km. Sortida a les 9.30 h del Molí del Foix. Passejada planera de connexió entre nuclis. Obsequi d'una peça de fruita i aigua. Inscripció prèvia a molidelfoix@smmonjos.cat o al 938 186 928. Campanya Metrominut i Setmana Europea de la Mobilitat.")
add("evt-20260919-trobada-dracs", "Trobada de Dracs - arribada i plantada", "2026-09-19", None, "18:00", None,
    "Davant de l'Ajuntament", "Altres", None, None,
    "Trobada de Dracs amb motiu del 45è Aniversari del Drac dels Monjos. Arribada i plantada dels dracs davant de l'ajuntament.")
add("evt-20260919-cercavila", "Trobada de Dracs - cercavila sense foc", "2026-09-19", None, "19:30", None,
    "Av. de Catalunya", "Altres", None, None,
    "Cercavila sense foc per l'av. de Catalunya fins al punt d'informació del mercat.")
add("evt-20260919-cercavila-foc", "Trobada de Dracs - cercavila de foc", "2026-09-19", None, "20:00", None,
    "Plaça de l'Església", "Altres", None, None,
    "Cercavila de foc fins a la plaça de l'Església.")
add("evt-20260919-concurs-enceses", "Trobada de Dracs - concurs d'enceses", "2026-09-19", None, "21:30", None,
    "Plaça de l'Església", "Altres", None, None,
    "Concurs d'enceses a la plaça de l'Església. Tot seguit, sopar popular (botifarra amb mongetes). Venda de tiquets el 16 de setembre de 19 h a 21 h davant l'ajuntament.")
add("evt-20260919-concert-ball", "Concert ball - Gina & The Tonics", "2026-09-19", None, "23:45", None,
    "Plaça de l'Església", "Música", None, None,
    "Concert ball a càrrec del grup Gina & The Tonics, amb motiu del 45è Aniversari del Drac dels Monjos.")
add("evt-20260920-sabors-guerra", "Sabors en temps de guerra", "2026-09-20", None, "09:00", None,
    "Subirats", "Altres", None, None,
    "Visita combinada entre Subirats i Santa Margarida i els Monjos. Sortida a les 9 h des de Subirats. El desplaçament entre ambdós punts es fa en cotxes particulars. Inscripció prèvia a escapadasingular.com.")
add("evt-20260920-memoria-guerra-aeria", "Memòria de la guerra aèria", "2026-09-20", None, "11:00", None,
    "Ciarga", "Altres", None, None,
    "Visita combinada entre el Ciarga i el Castell de Penyafort. Sortida a les 11 h des del Ciarga. El desplaçament entre el CIUDEB i el CIARGA es fa en cotxes particulars. Inscripció prèvia al 669 287 539.")
add("evt-20260920-visita-castell", "Visita guiada al Castell de Penyafort (turno 20/9)", "2026-09-20", None, "10:30", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. A les 10.30 h i a les 12 h. Imprescindible inscripció al 669 287 539.")
add("evt-20260920-visita-castell-2", "Visita guiada al Castell de Penyafort (12 h)", "2026-09-20", None, "12:00", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. Imprescindible inscripció al 669 287 539.")
add("evt-20260920-cinema", "Cinema: Tres Adioses", "2026-09-20", None, "19:00", None,
    "Societat La Margaridoia", "Altres", "3 euros", "4,5 euros",
    "Projecció de la pel·lícula 'Tres Adioses', d'Isabel Coixet, a la Societat La Margaridoia.")
add("evt-20260922-taller-matricules", "Taller de matrícules per a bicis i patinets", "2026-09-22", None, "17:30", None,
    "Molí del Foix", "Altres", None, None,
    "Taller de matrícules per a bicis i patinets. Si vens al Molí amb la bicicleta o patinet t'emportaràs un obsequi. Setmana Europea de la Mobilitat.")
add("evt-20260925-aula-cultural", "Aula cultural: Eulàlia i Mercè, una lluita pel matronatge de Barcelona", "2026-09-25", None, "17:00", None,
    "Casal de la gent gran", "Formació", None, None,
    "Xerrada 'Eulàlia i Mercè, una lluita pel matronatge de Barcelona' a càrrec de Marc Jobani.")
add("evt-20260926-sopar-ball", "Sopar-ball", "2026-09-26", None, "21:00", None,
    "Societat La Margaridoia", "Altres", None, None,
    "Sopar-ball a càrrec del grup Txic to txic. Preus i menú a determinar. Reserves: del 7 al 9 i del 14 al 16 de setembre, de 19 h a 21 h, a la secretaria de la societat. Per Whatsapp al 640 119 745 o a info@lamargaridoia.cat fins al dia 16.")
add("evt-20260926-ball-salo", "Ball de saló", "2026-09-26", None, "22:30", None,
    "Societat La Margaridoia", "Música", "gratuït", "7 euros",
    "Ball de saló a càrrec del duet Ruben's. Socis gratuït, públic 7 euros.")
add("evt-20260927-visita-castell", "Visita guiada al Castell de Penyafort (turno 27/9)", "2026-09-27", None, "10:30", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. A les 10.30 h i a les 12 h. Imprescindible inscripció al 669 287 539.")
add("evt-20260927-visita-castell-2", "Visita guiada al Castell de Penyafort (12 h)", "2026-09-27", None, "12:00", None,
    "Castell de Penyafort", "Altres", None, None,
    "Visita guiada al Castell de Penyafort. Imprescindible inscripció al 669 287 539.")
add("evt-20260927-teatre", "Teatre: Genitalmente hablando 2", "2026-09-27", None, "19:00", None,
    "Societat La Margaridoia", "Teatre", "gratuït", "8 euros",
    "Representació de l'obra 'Genitalmente hablando 2' a càrrec del grup Melodramatik's. Socis gratuït, públic 8 euros.")

# ---- Formació i cursos ----
add("evt-20260921-manualitats-mapa", "Club de la Feina: Dibuixa el teu mapa - visualitza el teu camí professional", "2026-09-21", None, "09:15", "12:15",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Curs del Club de la Feina: 'Dibuixa el teu mapa'. Dilluns 21 de setembre de 9.15 h a 12.15 h. Adreçat a persones en situació d'atur o en procés de millora de l'ocupació inscrites al Servei Local d'Ocupació o a la Xarxa Xaloc. Inscripcions al Club de la Feina o a clubdefeina@smmonjos.cat.")
add("evt-20260923-soft-skills", "Club de la Feina: Soft skills amb les mans", "2026-09-23", None, "09:15", "12:15",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Curs del Club de la Feina: 'Soft skills amb les mans'. Dimecres 23 de setembre de 9.15 h a 12.15 h. Adreçat a persones en situació d'atur del municipi o en procés de millora de l'ocupació.")
add("evt-20260928-mapa-talent", "Club de la Feina: Crea el teu mapa de Talent!", "2026-09-28", "2026-10-01", "09:00", "13:00",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Curs del Club de la Feina: 'Crea el teu mapa de Talent!'. Del 28 de setembre a l'1 d'octubre, de 9 h a 13 h. Places limitades. Inscripcions al Club de la Feina (dimarts i divendres de 10 h a 13 h), a Ca l'Antic (edifici Tangram) o a clubdefeina@smmonjos.cat.")
add("evt-20261001-dibuix-pintura", "Dibuix i pintura", "2026-10-01", None, "15:30", "17:45",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Curs de dibuix i pintura. Dilluns de 15.30 h a 17.45 h. Inici el 5 d'octubre, curs anual. Inscripcions a la web de l'ajuntament.")
add("evt-20260916-coral-penyafel", "Coral Amics de Penyafel (inici d'assajos)", "2026-09-16", None, "19:30", "21:30",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Assajos de la Coral Amics de Penyafel, dimecres de 19.30 h a 21.30 h a la Casa de Cultura Mas Catarro. Inici el 16 de setembre. Places limitades 13 (mínim 8 inscripcions). Inscripcions: 619 208 960 o coral.amics.penyafel@gmail.com.")
add("evt-20261001-coral-infantil-flabiol", "Coral Infantil El Flabiol (inici d'assajos)", "2026-10-01", None, "17:00", "18:00",
    "Casa de Cultura Mas Catarro", "Infantil", None, None,
    "Assajos de la Coral Infantil El Flabiol, dimecres de 17 h a 18 h. Inici el 2 d'octubre (assajos dimecres). Inscripcions al 667 467 497 o coralinfantilelflabiol@gmail.com.")
add("evt-20261001-coral-amistat", "Coral l'Amistat de la Ràpita (inici d'assajos)", "2026-10-01", None, "20:30", "22:00",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Assajos de la Coral l'Amistat de la Ràpita, dijous de 20.30 h a 22 h. Inscripcions: amistat.larapita@gmail.com o 679 467 335.")
add("evt-20261001-coral-bombeta", "Coral Infantil La Bombeta Màgica (inici d'assajos)", "2026-10-01", None, "17:00", "18:45",
    "Casa de Cultura Mas Catarro", "Infantil", None, None,
    "Assajos de la Coral Infantil La Bombeta Màgica, divendres de 17 h a 17.45 h (petits), de 17.15 h a 18.15 h (mitjans) i de 17.15 h a 18.45 h (grans). Inscripcions: coralinfantilbombetamagica@gmail.com.")
add("evt-20261001-cor-margaridoia", "Cor Margaridoia (inici d'assajos)", "2026-10-01", None, "19:30", "21:00",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Assajos del Cor Margaridoia, dimarts de 19.30 h a 21 h. Inscripcions: 657 839 001.")
add("evt-20261001-manualitats-casal-rapita", "Manualitats al casal de la gent gran (La Ràpita)", "2026-10-01", None, "15:30", "17:00",
    "Casal de la gent gran La Ràpita", "Formació", None, None,
    "Taller de manualitats al casal de la gent gran. La Ràpita, dilluns de 15.30 h a 17 h.")
add("evt-20261001-manualitats-casal-monjos", "Manualitats al casal de la gent gran (Els Monjos)", "2026-10-01", None, "17:00", "18:30",
    "Casal de la gent gran Els Monjos", "Formació", None, None,
    "Taller de manualitats al casal de la gent gran. Els Monjos, dimecres de 17 h a 18.30 h.")
add("evt-20261001-musicoterapia-rapita", "Musicoteràpia (La Ràpita)", "2026-10-01", None, "10:00", "11:00",
    "Casal de la gent gran La Ràpita", "Formació", None, None,
    "Musicoteràpia. La Ràpita, dilluns de 10 h a 11 h. Inscripcions a l'ajuntament.")
add("evt-20261001-musicoterapia-monjos", "Musicoteràpia (Els Monjos)", "2026-10-01", None, "17:00", "19:00",
    "Casal de la gent gran Els Monjos", "Formació", None, None,
    "Musicoteràpia. Els Monjos, dimarts de 17 h a 18 h i de 18 h a 19 h (dos grups). Inscripcions a l'ajuntament.")
add("evt-20260901-efa-inscripcions", "Inscripcions Escola d'Adults Fina Garcia Mateu", "2026-09-01", "2026-09-12", None, None,
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "Inscripcions a l'Escola de Formació de Persones Adultes Fina Garcia Mateu (cultura general, llengua catalana i castellana, perfeccionament del català, anglès i alemany, competències informàtiques i IA, preparació per a proves d'accés a cicles formatius). De l'1 al 12 de setembre: dilluns, dimarts, dimecres i dijous de 10 h a 13 h i dilluns i dimecres de 16 h a 18 h, a la Casa de Cultura Mas Catarro.")
add("evt-20261001-eso", "ESO - classe de formació", "2026-10-01", None, "17:00", "18:30",
    "Casa de Cultura Mas Catarro", "Formació", None, None,
    "ESO: dilluns de 17 h a 18.30 h. Inscripcions del 8 al 18 de setembre al web de l'ajuntament o presencialment de 10 h a 11 h a la masia Mas Catarro. Mínim 6 i màxim 12 infants/joves per grup. Preu 47 € trimestrals.")
add("evt-20260901-extraescolar-colors", "Pla Educatiu d'Entorn: Extraescolar en colors - Experimentació plàstica", "2026-09-01", None, None, None,
    "Casa de Cultura Mas Catarro", "Infantil", None, None,
    "Extraescolar en colors: Experimentació plàstica. De 1r a 3r, dimarts o dijous de 17 h a 18.30 h; de 4t a 6è, dimecres de 17 h a 18.30 h. A la Casa de Cultura Mas Catarro.")

# ---- ESPORTS: Activitats esportives (inscripcions de setembre) ----
add("evt-20260914-hoquei-i4i5", "Iniciació a l'hoquei (I4 i I5)", "2026-09-14", None, None, None,
    "Pista poliesportiva municipal", "Esport", None, None,
    "Iniciació a l'hoquei per a I4 i I5. Dilluns o dijous de 17 h a 18 h. Pista poliesportiva municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-psicomotricitat", "Psicomotricitat (Sant Domènec)", "2026-09-14", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Psicomotricitat. Dimarts de 16.30 h a 18 h. Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-psicomotricitat-arrels", "Psicomotricitat (Arrels)", "2026-09-14", None, None, None,
    "Escola Arrels", "Esport", None, None,
    "Psicomotricitat. Divendres de 16.30 h a 18 h. Escola Arrels. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-gimnastica-ritmica-i", "Gimnàstica rítmica (iniciació)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Gimnàstica rítmica. Dilluns i dimecres de 17 h a 18 h. Gimnàs municipal; divendres de 16.30 h a 18.30 h a l'Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-karate-inf", "Iniciació al karate (infants)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Iniciació al karate per a infants. Divendres de 17 h a 18 h. Gimnàs municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-patinatge-inf", "Iniciació al patinatge (infants)", "2026-09-14", None, None, None,
    "Pavelló municipal", "Esport", None, None,
    "Iniciació al patinatge. Dilluns de 17 h a 18 h. Pavelló municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-iniciacio-esport", "Iniciació a l'esport (1r i 2n de primària)", "2026-09-14", None, None, None,
    "Escola Doctor Samaranch / Escola Sant Domènec", "Esport", None, None,
    "Iniciació a l'esport per a 1r i 2n de primària. Dilluns de 16.30 h a 18 h a l'Escola Doctor Samaranch; dijous de 16.30 h a 18 h a l'Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-gimnastica-ritmica-prim", "Gimnàstica rítmica (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Gimnàstica rítmica. Dilluns i dimecres de 18 h a 19 h al gimnàs municipal; divendres de 16.30 h a 18.30 h a l'Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-karate-5e6e", "Iniciació al karate (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Iniciació al karate per a 5è i 6è de primària. Divendres de 17 h a 18 h. Gimnàs municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-patinatge-5e6e", "Iniciació al patinatge (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Pavelló municipal", "Esport", None, None,
    "Iniciació al patinatge. Dilluns de 17 h a 18 h. Pavelló municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-mini-volei-prim", "Mini vòlei (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Mini vòlei. Dimarts de 17 h a 18 h. Gimnàs institut El Foix. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-mini-basquet-prim", "Mini bàsquet (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Escola Doctor Samaranch", "Esport", None, None,
    "Mini bàsquet. Dijous de 16.30 h a 18 h. Escola Doctor Samaranch. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-padel-prim", "Iniciació al pàdel (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Pavelló municipal", "Esport", None, None,
    "Iniciació al pàdel. Divendres de 18 h a 19 h. Pavelló municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-lets-dance-prim", "Let's dance (5è i 6è de primària)", "2026-09-14", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Let's dance. Divendres de 18 h a 19 h. Gimnàs institut El Foix. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-gimnastica-ritmica-3i4eso", "Gimnàstica rítmica (3r i 4t de primària)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Gimnàstica rítmica. Dilluns i dimecres de 19 h a 20 h. Gimnàs municipal; divendres de 16.30 h a 18.30 h a l'Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-karate-3i4eso", "Iniciació al karate (1r i 2n d'ESO)", "2026-09-14", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Iniciació al karate. Divendres de 18 h a 19 h. Gimnàs municipal. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-futbol-sala-inf1", "Futbol sala (1r i 2n de primària)", "2026-09-14", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Futbol sala. Dilluns i dijous de 17 h a 18 h. Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-futbol-sala-inf2", "Futbol sala (3r i 4t de primària)", "2026-09-14", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Futbol sala. Dilluns i dijous de 17 h a 18 h. Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-futbol-sala-es", "Futbol sala (1r i 2n d'ESO)", "2026-09-14", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Futbol sala. Dilluns i dijous de 18 h a 19 h. Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-futbol-sala-3i4", "Futbol sala (3r i 4t d'ESO)", "2026-09-14", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Futbol sala. Dilluns i dijous de 18 h a 19 h. Escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-mini-volei-3i4eso", "Mini vòlei (3r i 4t d'ESO)", "2026-09-14", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Mini vòlei. Dimarts i dijous de 18 h a 19 h. Gimnàs institut El Foix. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-mini-volei-1i2eso", "Mini vòlei (1r i 2n d'ESO)", "2026-09-14", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Mini vòlei. Dimarts i dijous de 17 h a 18 h. Gimnàs institut El Foix. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-mini-basquet-eso", "Mini bàsquet (ESO)", "2026-09-14", None, None, None,
    "Escola Arrels / Gimnàs institut El Foix", "Esport", None, None,
    "Mini bàsquet. Dilluns de 17 h a 18 h a l'Escola Arrels; dimecres de 17 h a 18 h al gimnàs institut El Foix; i dimarts i dijous de 19 h a 20 h al gimnàs escola Sant Domènec. Inscripcions a partir del 14 de setembre.")
add("evt-20260914-balls-moderns-3i4", "Balls moderns (3r i 4t d'ESO)", "2026-09-14", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Balls moderns. Divendres de 19 h a 20 h. Gimnàs institut El Foix. Inscripcions a partir del 14 de setembre.")
add("evt-20260907-gimnastica-manteniment", "Gimnàstica de manteniment", "2026-09-07", None, None, None,
    "Gimnàs escola Sant Domènec", "Esport", None, None,
    "Gimnàstica de manteniment. Dilluns i dimecres de 19.15 h a 20.15 h. Gimnàs escola Sant Domènec. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-gimnastica-terapeutica", "Gimnàstica terapèutica i salut", "2026-09-07", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Gimnàstica terapèutica i salut. Dilluns i dimecres de 16 h a 17 h, i dimarts i dijous de 9.15 h a 10.15 h i de 10.15 h a 11.15 h. Gimnàs municipal. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-marxes-nordiques", "Marxes nòrdiques", "2026-09-07", None, None, None,
    "Camp de futbol", "Esport", None, None,
    "Marxes nòrdiques. Divendres de 9.30 h a 11 h. Camp de futbol. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-qi-jong", "Qi Jong", "2026-09-07", None, None, None,
    "Escoles velles de la Ràpita", "Esport", None, None,
    "Qi Jong. Dimarts de 10 h a 11 h. Escoles velles de la Ràpita. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-ioga", "Ioga", "2026-09-07", None, None, None,
    "Gimnàs escola Samaranch i Fina", "Esport", None, None,
    "Ioga. Dilluns i dimecres de 17 h a 18.30 h i de 18.30 h a 20 h. Gimnàs escola Samaranch i Fina. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-pilates", "Pilates", "2026-09-07", None, None, None,
    "Gimnàs municipal", "Esport", None, None,
    "Pilates. Dimarts i dijous de 18 h a 19 h, de 19 h a 20 h i de 20 h a 21 h. Gimnàs municipal. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-futbol-sala-adults", "Futbol sala (adults)", "2026-09-07", None, None, None,
    "Escola Sant Domènec", "Esport", None, None,
    "Futbol sala per a adults. Dilluns i dijous de 17 h a 18 h. Escola Sant Domènec. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-mini-volei-adults", "Mini vòlei (adults)", "2026-09-07", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Mini vòlei per a adults. Dimarts i dijous de 18 h a 19 h. Gimnàs institut El Foix. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-padel-adults", "Iniciació al pàdel (adults)", "2026-09-07", None, None, None,
    "Pavelló municipal", "Esport", None, None,
    "Iniciació al pàdel per a adults. Divendres de 18 h a 19 h. Pavelló municipal. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-hoquei-adults", "Hoquei (adults)", "2026-09-07", None, None, None,
    "Pista poliesportiva municipal", "Esport", None, None,
    "Hoquei per a adults. Dilluns o dijous de 17 h a 18 h. Pista poliesportiva municipal. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-balls-moderns-adults", "Balls moderns (adults)", "2026-09-07", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Balls moderns per a adults. Divendres de 19 h a 20 h. Gimnàs institut El Foix. Inscripcions a partir del 7 de setembre.")
add("evt-20260907-lets-dance-adults", "Let's dance (adults)", "2026-09-07", None, None, None,
    "Gimnàs institut El Foix", "Esport", None, None,
    "Let's dance per a adults. Divendres de 18 h a 19 h. Gimnàs institut El Foix. Inscripcions a partir del 7 de setembre.")

# ---- Notícies datades ----
add("evt-20261002-casa-dels-passos", "Obertura Casa dels Passos Petits", "2026-10-02", None, "10:00", "12:00",
    "Carrer d'Anselm Clavé 9", "Infantil", None, "gratuït",
    "Casa dels Passos Petits, espai per a infants de 0 a 3 anys i les famílies, obre el nou curs el dia 2 d'octubre. Obert dimarts i divendres de 10 h a 12 h, dilluns de 16.45 h a 18.30 h, i el primer i últim dimecres de cada mes. Servei gratuït, no cal inscripció prèvia.")
add("evt-20261001-ludoteca-baldufa-inici", "Inici de curs de la Ludoteca La Baldufa", "2026-10-01", None, "16:45", "18:30",
    "Carrer d'Anselm Clavé 9", "Infantil", None, None,
    "La Ludoteca La Baldufa inicia el curs el dia 1 d'octubre, els dimarts i dijous de 16.45 h a 18.30 h. Inscripcions presencials a la jornada de portes obertes del 8 de setembre o telemàtiques al web de l'ajuntament des del 8 de setembre.")
add("evt-20261001-teva-veu-importa", "Taller de teatre 'La teva veu importa'", "2026-10-01", None, None, None,
    "Santa Margarida i els Monjos", "Teatre", None, None,
    "Taller de teatre 'La teva veu importa', adreçat a dones, els dimarts al matí a partir d'octubre. Inscripcions per correu a igualtat@smmonjos.cat amb nom i telèfon de contacte.")
add("evt-20261015-prohibicio-foc", "Fi de la prohibició de foc en terreny forestal", "2026-10-15", None, None, None,
    "Santa Margarida i els Monjos", "Altres", None, None,
    "Fins al 15 d'octubre no es pot encendre foc en terreny forestal ni en la franja de 500 metres que l'envolta.")

data = {
    "municipio": "Santa Margarida i els Monjos",
    "mes": "Setembre 2026",
    "fuente_pdf": "https://www.santamargaridaielsmonjos.cat/fitxer/9839/AGENDA%20Setembre%2026_web.pdf",
    "generado_por": "opencode-go/deepseek-v4-pro",
    "eventos": ev,
}

out = "/root/.openclaw/workspace/agenda-smmonjos-mvp/.context/eventos_luna.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Validate
with open(out, encoding="utf-8") as f:
    loaded = json.load(f)

# Count
with open(out, "a", encoding="utf-8") as f:
    pass

# Write count to a separate marker by rewriting? Keep count via a summary file
with open("/root/.openclaw/workspace/agenda-smmonjos-mvp/.context/eventos_count.txt", "w", encoding="utf-8") as f:
    f.write(str(len(loaded["eventos"])))

print("TOTAL EVENTOS:", len(loaded["eventos"]))
print("VALID JSON OK")
