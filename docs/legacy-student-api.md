# Legacy Student API Notes

## Endpoint osservati

### Compiti

- Endpoint range supportato: `/api-studente/v1/alunno/{student_id}/compito/elenco/{start}/{end}`
- Query param richiesto: `contextAlunno={student_id}`
- Esempio verificato: `GET /api-studente/v1/alunno/9009/compito/elenco/09-03-2026/15-03-2026?contextAlunno=9009`

## Implicazioni implementative

- Per i compiti non serve piu' fare una richiesta per ogni giorno.
- Il default applicativo puo' usare una singola chiamata su una finestra corta, oggi `+14 giorni`.
- Questo endpoint e' il candidato corretto per polling leggero e notifiche di nuovi compiti.
