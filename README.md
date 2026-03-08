# Nuvola API

`nuvola-api` e' un client Python non ufficiale per Nuvola pensato sia come libreria sia come CLI.

## Disclaimer

Il progetto non e' affiliato con Madisoft. Flussi di login, endpoint e payload possono cambiare senza preavviso.

## Stato supporto backend

- Obiettivo architetturale: backend tenant-first.
- Backend `legacy_student_api`: parity minima utile implementata.
- Backend `tenant_api`: struttura pronta, metodi non ancora implementati.

## Struttura

```text
docs/
src/nuvola/domain/
src/nuvola/application/
src/nuvola/adapters/tenant_api/
src/nuvola/adapters/legacy_student_api/
src/nuvola/adapters/storage/
src/nuvola/cli/
tests/unit/
tests/integration/fixtures/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/nuvola-api-pyc python3 -m py_compile $(find src tests -name '*.py')
```

## Uso come libreria

```python
from nuvola import NuvolaService
from nuvola.adapters.legacy_student_api import LegacyStudentApiAdapter
from nuvola.adapters.storage.file_session_store import FileSessionStore

service = NuvolaService(
    backends={"legacy_student": LegacyStudentApiAdapter()},
    session_store=FileSessionStore(),
)
```

## Uso CLI

```bash
nuvola-cli
```

Variabili ambiente supportate:

- `NUVOLA_BACKEND=legacy_student`
- `NUVOLA_BACKEND=tenant`
- `NUVOLA_TENANT=<tenant>`

La CLI usa esclusivamente il layer applicativo per login, ripresa sessione, selezione studente e report.
