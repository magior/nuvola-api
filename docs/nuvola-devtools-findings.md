# Nuvola DevTools Findings

Osservazioni sui flussi UI e sugli endpoint usati da `https://nuvola.madisoft.it`.

Nota: esempi, nomi di materia/docente, identificativi e riferimenti scolastici riportati qui sono anonimizzati o parametrizzati.

## Flusso di autenticazione

- Login web classico sulla pagina `/login`
- Cookie `nuvola` di sessione web
- `GET /api-studente/v1/login-from-web`
- Token Bearer usato per tutte le richieste `api-studente/v1/...`

Questo flusso e' coerente con il backend `legacy_student` usato da `nuvola-api`.

## Endpoint usati dalla UI

Per lo studente selezionato la UI usa almeno questi endpoint:

- `GET /api-studente/v1/alunni`
- `GET /api-studente/v1/alunno/{id}/menu?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/notifiche/conteggio?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/help/news?...`
- `GET /api-studente/v1/alunno/{id}/compito/elenco/{data}?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/argomento-lezione/elenco/{data}?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/voti?contextAlunno={id}&limit=10`
- `GET /api-studente/v1/alunno/{id}/frazioni-temporali?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/frazione-temporale/{periodo}/voti/materie?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/frazione-temporale/{periodo}/voti/materia/{materia}?contextAlunno={id}`
- `GET /api-studente/v1/alunno/{id}/assenze?...`
- `GET /api-studente/v1/alunno/{id}/note?...`
- `GET /api-studente/v1/alunno/{id}/eventi-classe?...`
- `GET /api-studente/v1/alunno/{id}/eventi-classe-materia?...`
- `GET /api-studente/v1/alunno/{id}/eventi-alunno?...`
- `GET /api-studente/v1/alunno/{id}/pagamenti?...`

Il bot oggi usa direttamente solo studenti, compiti, argomenti e voti.

## Campi rilevanti confermati

Gli esempi di campo qui sotto sono volutamente descrittivi e non riportano valori identificativi reali.

I compiti restituiti dalla UI includono gia':

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

Il bot usa gia' `dataAssegnazione`, ma non usa ancora `docente`, `nomeArgomento` o `allegati`.

I latest grades mostrati in home includono almeno:

- `nomeMateria`
- `idMateria`
- `idFrazioneTemporale`
- `data`
- `docente`
- `tipologia`
- `valutazione`
- `valutazioneMatematica`
- `faMedia`
- `peso`
- `descrizione`
- `obiettivi[]`

## Decisione implementativa

Il bot ora usa l'endpoint `menu` come preflight per le sezioni che interroga:

- `compito_accesso_lista`
- `argomento_lezione_accesso_lista`
- `voto_accesso_sezione_abilitato`

Se Nuvola dichiara la sezione disabilitata per uno studente, il bot salta la richiesta di dettaglio invece di generare `403` rumorosi.

## Caso reale verificato

Per uno studente con accesso limitato ai voti la UI espone nel `menu`:

- `voto_accesso_sezione_abilitato = false`

Quindi i `403` sui voti osservati nei log non erano un problema di autenticazione, ma un vincolo reale di accesso per quello studente.
