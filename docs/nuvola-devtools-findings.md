# Nuvola DevTools Findings

Osservazioni sui flussi UI e sugli endpoint usati da `https://nuvola.madisoft.it`.

Nota: esempi, nomi di materia/docente, identificativi e riferimenti scolastici riportati qui sono anonimizzati o parametrizzati.

## Flusso di autenticazione

Aggiornato al 2026-09-17: Nuvola e' passata a Keycloak (OIDC authorization code).
Il vecchio flusso Symfony (`GET /` con form `_csrf_token`, poi `POST /login_check`)
non esiste piu'.

1. `GET /connect/authentication-service` -> 302 verso
   `https://auth.nuvola.madisoft.it/realms/nuvola/protocol/openid-connect/auth`
   con `client_id=web` e `redirect_uri=/connect/authentication-service/check`.
   La pagina `/login` e' solo un interstiziale JS che rimbalza qui, quindi un
   client senza browser parte direttamente da questo URL.
2. La pagina di login Keycloak usa il tema `nuvola-theme`, una SPA React: il
   body e' solo `<div id="root">`. Il form va costruito a mano leggendo
   `kcContext.url.loginAction` dallo `<script>` inline nell'head, che contiene
   gia' `session_code` ed `execution`.
3. `POST` su quel `loginAction` con i campi `username`, `password`, `credentialId`.
4. Redirect su `/connect/authentication-service/check?code=...&state=...`, che
   setta il cookie `nuvola` di sessione web.
5. `GET /api-studente/v1/login-from-web` con quel cookie: invariato, restituisce
   `token` (JWT) piu' `refreshToken`, `aree`, `richiesto2FA` e altri campi.
6. Token Bearer usato per tutte le richieste `api-studente/v1/...`

Dal punto 1 al 5 sono tutti redirect HTTP: nessun passaggio richiede JavaScript,
l'unico lavoro manuale e' il POST del punto 3.

Il direct grant di Keycloak non e' utilizzabile: `POST /protocol/openid-connect/token`
con `grant_type=password&client_id=web` risponde `401 unauthorized_client`.

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
