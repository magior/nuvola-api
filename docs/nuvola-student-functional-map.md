# Nuvola Student Functional Map

Mappa funzionale del profilo studente su Nuvola, con esempi e riferimenti anonimizzati.

Nota: esempi, nomi di materie/docenti, identificativi e riferimenti scolastici riportati in questo documento sono anonimizzati o parametrizzati.

## Obiettivo

Mappare il perimetro API/UI del profilo studente su Nuvola per preparare una futura integrazione `student mode` nel bot, mantenendo come baseline il comportamento gia' osservato sul profilo genitore.

## Flusso di autenticazione

Il flusso osservato e' coerente con il backend `legacy_student` gia' usato nel progetto:

- login web sulla pagina `/login`
- cookie `nuvola` di sessione web
- `GET /api-studente/v1/login-from-web`
- token Bearer per tutte le richieste `api-studente/v1/...`

La differenza principale non e' nell'autenticazione ma nella UI di destinazione:

- genitore: `https://nuvola.madisoft.it/area-tutore`
- studente: `https://nuvola.madisoft.it/area-studente`

## Modello di accesso osservato

Anche sul profilo studente la UI usa ancora il contesto `alunno/{id}` nelle API.

Endpoint base usati subito dopo il login:

- `GET /api-studente/v1/alunni`
- `GET /api-studente/v1/alunno/{student_id}/menu?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/notifiche/conteggio?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/help/news?...`

Questo significa che, lato integrazione bot, il profilo studente puo' probabilmente riusare gran parte del modello corrente:

- stesso backend
- stesso token API
- stesso concetto di `student_id`
- stessa utilita' dell'endpoint `menu` come preflight per le sezioni abilitate

## Menu e differenze rispetto al profilo genitore

Dal `menu` del profilo studente risultano abilitate le sezioni principali:

- `voto_accesso_sezione_abilitato = true`
- `assenza_accesso_sezione_abilitato = true`
- `nota_accesso_sezione_abilitato = true`
- `argomento_lezione_accesso_lista = true`
- `compito_accesso_lista = true`
- `questionario_accesso_lista = true`
- `materiale_per_docente_abilita_gestione = true`
- `abilita_gestione_colloqui = true`
- `abilita_gestione_modulistica = true`
- `abilita_gestione_pagamenti = true`

Funzioni assenti o disabilitate nel profilo osservato:

- `scrutinio_documento_accesso_lista = false`
- `abilita_fascicolo_alunno = false`
- `abilita_consegna_tesina_esame = false`
- `abilita_richiesta_credenziali_invalsi = false`
- `abilita_delegati_al_ritiro = false`
- `abilita_pcto = false`

Differenze visibili rispetto al profilo genitore:

- la navigazione studente non mostra `Documenti scrutinio`
- `Questionari` e' presente e attivo
- `Materiale per docente` non e' solo consultazione: la UI espone anche la creazione di nuovo materiale

## Mappa funzionale route -> endpoint

### Home

Route:

- `/area-studente`

Endpoint principali:

- `GET /api-studente/v1/alunno/{student_id}/compito/elenco/{date}?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/argomento-lezione/elenco/{date}?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/eventi-classe?...`
- `GET /api-studente/v1/alunno/{student_id}/eventi-classe-materia?...`
- `GET /api-studente/v1/alunno/{student_id}/eventi-alunno?...`
- `GET /api-studente/v1/alunno/{student_id}/assenze?contextAlunno={student_id}&limit=10`
- `GET /api-studente/v1/alunno/{student_id}/note?contextAlunno={student_id}&limit=10`
- `GET /api-studente/v1/alunno/{student_id}/voti?contextAlunno={student_id}&limit=10`
- `GET /api-studente/v1/alunno/{student_id}/pagamenti?contextAlunno={student_id}&filter[stato]=daPagare&page=1&limit=10`

Note:

- La home studente e' un aggregatore ricco, come quella genitore.
- I compiti e gli argomenti mostrati sono coerenti con gli endpoint gia' usati dal progetto.

### Voti

Route:

- `/area-studente/voti`
- `/area-studente/voti/{subject_id}`

Endpoint principali:

- `GET /api-studente/v1/alunno/{student_id}/voti?contextAlunno={student_id}&limit=10`
- `GET /api-studente/v1/alunno/{student_id}/frazioni-temporali?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/frazione-temporale/{period_id}/voti/materie?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/frazione-temporale/{period_id}/voti/materia/{subject_id}?contextAlunno={student_id}`

Differenze importanti rispetto al profilo genitore:

- sul profilo studente `voto_dettaglio_mostra_valore_matematico = true`
- sul profilo studente `voto_dettaglio_mostra_fa_media = true`
- la home studente mostra `valutazione` gia' numerica anche dove il profilo genitore mostrava valori simbolici come `*`
- nei payload compaiono sia `valutazione` sia `valutazioneMatematica`
- la home richiama `voti?limit=10` come lista trasversale degli ultimi voti, separata dal dettaglio per materia

Implicazione per la futura integrazione:

- in modalita' studente conviene dare priorita' a `valutazioneMatematica` quando presente, o quantomeno conservarla insieme al valore formattato.

### Assenze

Route:

- `/area-studente/assenze`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/assenze?contextAlunno={student_id}&limit=10`

Note:

- gia' presente in home
- non sono emerse differenze sostanziali rispetto alla controparte genitore nella prima analisi

### Note

Route:

- `/area-studente/note`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/note?contextAlunno={student_id}&limit=10`

### Argomenti di lezione

Route:

- `/area-studente/argomenti-lezione`
- `/area-studente/argomenti-lezione/{lesson_id}`

Endpoint principali:

- `GET /api-studente/v1/alunno/{student_id}/argomento-lezione/elenco/{date}?contextAlunno={student_id}`

Campi confermati:

- `id`
- `materia`
- `docente`
- `tipo`
- `nomeArgomento`
- `annotazioni`
- `descrizioneEstesa`
- `compresenza`
- `allegati`
- `cofirme`
- `video_youtube`
- informazioni orarie per giornata

### Compiti

Route:

- `/area-studente/compiti`

Endpoint principali:

- `GET /api-studente/v1/alunno/{student_id}/compito/elenco/{date}?contextAlunno={student_id}`

Campi confermati:

- `docente`
- `materia`
- `nomeArgomento`
- `idArgomento`
- `dataAssegnazione`
- `dataConsegna`
- `descrizioneCompito`
- `allegati`
- `classe`
- `classeId`

Lo shape e' sostanzialmente identico al profilo genitore.

### Calendario

Route:

- `/area-studente/calendario`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/eventi-classe?contextAlunno={student_id}&soloVisibiliPlanner=true`

Note:

- la UI mese/settimana/giorno del calendario sembra basarsi almeno sugli eventi planner visibili
- e' una funzionalita' distinta dalla lista `Documenti ed Eventi`

### Documenti ed Eventi

Route:

- `/area-studente/documenti-eventi`
- tab interni per eventi classe, eventi materia, eventi alunno

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/eventi-classe.schema?contextAlunno={student_id}`
- `GET /api-studente/v1/alunno/{student_id}/eventi-classe?contextAlunno={student_id}&filter[ordinamento]=data_inizio_desc&page=1&limit=25`

Endpoint gia' visti in home e logicamente correlati:

- `GET /api-studente/v1/alunno/{student_id}/eventi-classe-materia?...`
- `GET /api-studente/v1/alunno/{student_id}/eventi-alunno?...`

Note:

- la presenza di `.schema` suggerisce una UI guidata da metadata di colonna/filtro
- e' probabile che anche le viste materia/alunno abbiano endpoint o schema paralleli

### Materiale per docente

Route:

- `/area-studente/materiali-per-docente`
- `/area-studente/materiali-per-docente/nuovo`

Endpoint osservati:

- `GET /api-studente/v1/materiali-per-docente?contextAlunno={student_id}`
- `GET /api-studente/v1/materiali-per-docente/nuovo.schema?contextAlunno={student_id}`
- `GET /api-studente/v1/materiali-per-docente/nuovo?contextAlunno={student_id}`

Funzionalita' notevoli:

- la UI permette la creazione di nuovo materiale
- il form studente contiene:
  - `Oggetto`
  - `Note`
  - selezione `Docente`
  - selezione `Materia`
  - upload allegati

Questo e' un punto nuovo rispetto al perimetro attuale del bot e merita attenzione separata:

- non e' solo lettura
- richiede probabilmente POST multipart o upload file
- il `.schema` e l'endpoint `nuovo` sembrano fornire metadata e lookup del form

### Colloqui

Route:

- `/area-studente/colloqui`
- link secondari:
  - `/area-studente/colloqui/selezione-docente`
  - `/area-studente/colloqui/svolti`
  - `/area-studente/colloqui/selezione-docente?type=solo-visione`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/colloqui/prenotati?contextAlunno={student_id}`

Note:

- la UI distingue almeno prenotati, svolti e non prenotabili
- resta da esplorare la parte di selezione docente e la creazione/prenotazione effettiva

### Bacheche

Route:

- `/area-studente/bacheche`

Endpoint osservati:

- `GET /api-studente/v1/bacheche-digitali?fields=id,nome&metadata=count,actions&limit=1000&contextAlunno={student_id}`

Note:

- endpoint dedicato, diverso dal namespace `alunno/{id}/...`
- la presenza di `actions` nei metadata lascia intendere operazioni o stati oltre alla sola lista

### Questionari

Route:

- `/area-studente/questionari`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/questionari?contextAlunno={student_id}`

Note:

- sul profilo osservato la lista e' vuota
- resta da esplorare il dettaglio e la sottomissione di un questionario attivo

### Modulistica

Route:

- `/area-studente/modulistica/moduli`
- `/area-studente/modulistica/compilati?compilati=true&bozze=true`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/moduli-compilabili?contextAlunno={student_id}`

Note:

- la UI mostra anche la sezione `Moduli compilati`, ma in questa analisi non e' stata aperta
- e' probabile esista un endpoint parallelo per bozze/compilati

### Pagamenti

Route:

- `/area-studente/pagamenti`

Endpoint osservati:

- `GET /api-studente/v1/alunno/{student_id}/pagamenti?contextAlunno={student_id}&filter[stato]=daPagare&page=1&limit=10`

## Differenze funzionali principali vs profilo genitore

- Base route diversa: `area-studente` invece di `area-tutore`
- Nessuna selezione multi-studente visibile come concetto operativo principale, anche se le API continuano a usare `alunno/{id}`
- `Questionari` e' attivo e visibile
- `Documenti scrutinio` non compare nella navigazione osservata
- `Materiale per docente` consente creazione/upload lato studente
- I voti studente espongono valori numerici e `valutazioneMatematica`, mentre il profilo genitore puo' mostrare valori piu' “editoriali” o simbolici nella panoramica

## Raccomandazioni per la futura implementazione `student mode`

- Riutilizzare il backend `legacy_student` e il flusso auth gia' esistente
- Introdurre una modalita' o profilo di accesso separato a livello config, ma mantenere invariato il modello session/token
- Continuare a usare `menu` come preflight per sezione anche in modalita' studente
- Per i voti, conservare sia `valutazione` sia `valutazioneMatematica`
- Prevedere una distinzione esplicita tra endpoint di sola lettura e endpoint operativi:
  - sola lettura: compiti, argomenti, assenze, note, eventi, pagamenti
  - operativi o semi-operativi: colloqui, materiali per docente, questionari, modulistica
- Introdurre un layer di capability mapping per evitare di hardcodare le differenze genitore/studente nei formatter

## Aree ancora da esplorare prima di implementare tutte le API studente

- Dettaglio e submit di `questionari`
- Elenco `moduli compilati` e gestione bozze
- Prenotazione colloqui e flusso `selezione-docente`
- POST/upload reale per `materiali-per-docente/nuovo`
- Dettaglio singola bacheca e azioni disponibili
- Dettaglio eventi materia/alunno e relativi endpoint `.schema`, se presenti

## Conclusione

Il profilo studente non richiede un backend completamente diverso: l'asse API e' lo stesso gia' usato nel progetto. Le differenze reali stanno in:

- route UI
- flag del `menu`
- semantica e ricchezza di alcuni payload
- presenza di funzionalita' operative aggiuntive, soprattutto `Questionari`, `Colloqui`, `Modulistica` e `Materiale per docente`

Questo rende plausibile un'estensione incrementale del bot verso una `student mode`, partendo dalle sezioni read-only gia' vicine al supporto esistente e rinviando i flussi write/upload a una fase successiva.
