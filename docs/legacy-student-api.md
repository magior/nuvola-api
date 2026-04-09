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

## Implicazioni implementative

- Per i compiti non serve piu' fare una richiesta per ogni giorno.
- Il default applicativo puo' usare una singola chiamata su una finestra corta, oggi `+14 giorni`.
- Questo endpoint e' il candidato corretto per polling leggero e notifiche di nuovi compiti.
- Per i voti conviene distinguere tra:
  - endpoint home `voti?limit=<n>` per gli ultimi voti trasversali
  - endpoint per pagina dettaglio `frazioni-temporali`, `voti/materie`, `voti/materia/{subject_id}`
