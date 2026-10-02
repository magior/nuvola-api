# Legacy Student API Notes

Nota: esempi, identificativi, nomi di materia e docenti riportati in questa directory sono intenzionalmente anonimizzati.

## Endpoint osservati

### Compiti

- Endpoint range supportato: `/api-studente/v1/alunno/{student_id}/compito/elenco/{start}/{end}`
- Query param richiesto: `contextAlunno={student_id}`
- Esempio verificato: `GET /api-studente/v1/alunno/{student_id}/compito/elenco/{start}/{end}?contextAlunno={student_id}`

### Ultimi voti

- Endpoint home/widget osservato: `/api-studente/v1/alunno/{student_id}/voti`
- Query param richiesti: `contextAlunno={student_id}`, `limit=<n>`
- Shape rilevante confermato:
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

### Bacheche e circolari

- Le circolari sono documenti di una bacheca digitale; dettaglio completo in `nuvola-student-functional-map.md`.
- Implementato in sola lettura:
  - `bacheche-digitali/{board_id}/documenti` (lista, `mostraArchiviati` opzionale)
  - `bacheche-digitali/{board_id}/documenti/{document_id}` (dettaglio con allegati)
  - `alunno/{student_id}/file-preview/{attachment_uuid}` (contenuto binario dell'allegato)
  - `alunno/{student_id}/notifiche/bacheche` e `alunno/{student_id}/notifiche/conteggio`
- `POST .../documenti/{document_id}/segna-letto` non viene mai chiamato: leggere un documento dal client
  non lo marca come letto in Nuvola.
- `fields` e' valorizzato con le chiavi osservate nelle risposte della UI.
- La lista documenti pagina con `offset` + `limit` (default 25); `_collection_count` in `raw` indica il totale.
- Per `notifiche/bacheche` i valori di `fields`, `limit` e `orderBy[data]` sono dedotti, non catturati.

## Implicazioni implementative

- Per i compiti non serve piu' fare una richiesta per ogni giorno.
- Il default applicativo puo' usare una singola chiamata su una finestra corta, oggi `+14 giorni`.
- Questo endpoint e' il candidato corretto per polling leggero e notifiche di nuovi compiti.
- Per i voti conviene distinguere tra:
  - endpoint home `voti?limit=<n>` per gli ultimi voti trasversali
  - endpoint per pagina dettaglio `frazioni-temporali`, `voti/materie`, `voti/materia/{subject_id}`
