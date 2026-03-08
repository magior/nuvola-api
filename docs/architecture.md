# Architecture

## Layers

- `domain`: entita' e contratti indipendenti da I/O.
- `application`: use case, policy di sessione, helper date e renderer testuali.
- `adapters`: backend HTTP e storage locale.
- `cli`: interfaccia terminale che dipende solo da `application`.

## Backend strategy

- `tenant_api` e' il target architetturale di lungo periodo.
- `legacy_student_api` fornisce la parity minima utile per una V1 pubblica.
- La scelta del backend e' esterna al dominio e arriva da configurazione o sessione persistita.

## Session lifecycle

1. `login` autentica tramite adapter e produce `SessionContext`.
2. Il token viene persistito subito in `.nuvola-session.json`.
3. `list_students` recupera gli alunni disponibili.
4. `select_student` aggiorna `student_id` e ripersistisce backend, tenant e token.
5. `resume_session` permette di riprendere il lavoro senza nuove credenziali se il token e' ancora valido.

## Use cases

- `login`
- `resume_session`
- `select_student`
- `list_students`
- `list_grade_periods`
- `list_subject_grades`
- `list_homework`
- `list_lesson_topics`

## Adapter responsibilities

- `legacy_student_api`: gestisce login web, `login-from-web` e gli endpoint legacy studente.
- `tenant_api`: espone lo scheletro del backend tenant documentato, ma oggi solleva `NotImplementedError` con messaggi espliciti.
- `storage.file_session_store`: persiste localmente backend, tenant, token e `student_id`.
