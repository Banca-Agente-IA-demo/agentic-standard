# Tasks: Prueba de humo de la organización

**Input**: Design documents from `/specs/001-smoke-org/`

**Prerequisites**: plan.md (estructura reducida del 2026-09-07), spec.md, research.md, data-model.md,
contracts/cli.md, quickstart.md

**Tests**: obligatorias (constitución IV, T1 a T6). Se escriben antes que el código que cubren.

**Revisión del 2026-09-07**: la lista original de 45 tareas se redujo a 16. Se eliminó la historia 3
(diferida al hito 8) y la estructura por capas con puerto formal; se conservan CI, pruebas con datos y
fixtures reales.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 `pyproject.toml`: `requires-python = ">=3.11"`, sin dependencias de ejecución,
      `dev = ["pytest"]`, script `smoke-org`, paquetes bajo `tools/`, `testpaths = ["tests"]`.
- [ ] T002 [P] `.github/workflows/tests.yml`: `pull_request` a `main` filtrado por rutas,
      `permissions: contents: read`, job `tests` con matriz 3.11 y 3.12, acciones por SHA,
      `pip install -e ".[dev]"` y `pytest -q`.
- [ ] T003 Esqueleto: `tools/smoke_org/__init__.py`, `tests/smoke_org/__init__.py`,
      `tests/smoke_org/fixtures/`; `pip install -e ".[dev]"` y `pytest -q` en verde con cero pruebas.

## Phase 2: Dominio (US1 y US2)

- [ ] T004 [P] `tests/smoke_org/test_model.py`: veredicto (pasa, un fallo basta, sin datos prevalece,
      cada veredicto con su código en bucle) y validación del entorno (canales distintos, sin repos
      repetidos, organización no vacía).
- [ ] T005 [P] `tests/smoke_org/test_checks.py`: una prueba por comprobación y defecto, incluidas:
      cada campo de la organización, equipo ausente, App ausente / `all` / `selected` completa /
      `selected` incompleta, secreto con nombre casi igual, canal cruzado, topic en repo no dominio,
      ruleset con otro nombre o no activo, contexto de menos, de más y mal escrito, `integration_id`
      distinto, y `Unavailable` produce `UNCHECKED` en cada comprobación.
- [ ] T006 `tools/smoke_org/model.py`: constantes contrato, `IndexChannel`, `Marketplace`,
      `Environment`, `validate_environment`, `Unavailable`, tipos observados, `OrganizationSnapshot`,
      `CheckStatus`, `CheckResult`, `Report`, `Verdict`, `verdict_of`. Sin I/O.
- [ ] T007 `tools/smoke_org/checks.py`: las ocho comprobaciones puras y `CHECKS`; `run_checks(snapshot,
      environment, roster) -> Report` recorre todas.

## Phase 3: Adaptadores y entry point (US1 y US2)

- [ ] T008 [P] `tests/smoke_org/fixtures/`: respuestas reales medidas el 2026-09-07 con `README.md`
      (comando, fecha, organización): `org.json`, `teams.json`, `installations.json`,
      `secret_list.json`, `variable_list.json`, `repo_list_topic.json`, `rulesets_list.json`,
      `ruleset_protect_main.json`, `ruleset_protect_tags.json`, `gh_forbidden.json`,
      `gh_no_session.txt`.
- [ ] T009 [P] `tests/smoke_org/test_gh_reader.py`: `FakeRunner` por comando; parseo de cada
      fixture; sin sesión y 403 devuelven `Unavailable` con mensaje; comandos como listas; el lector
      pide el detalle de cada ruleset.
- [ ] T010 [P] `tests/smoke_org/test_files.py` (`tmp_path`): clave desconocida es error, JSON
      inválido es error, el roster recorre todos los papeles del `config/teams.json` real.
- [ ] T011 [P] `tests/smoke_org/test_text_report.py`: etiqueta entre corchetes, esperado y
      encontrado, resumen y veredicto.
- [ ] T012 `tools/smoke_org/gh_reader.py`: `CommandRunner` Protocol con default `subprocess.run`
      inyectable, `GhReader(organization, runner)` con un método por pieza y `snapshot(environment)`;
      comandos de research.md R6; errores a `Unavailable`; `DEBUG` por comando.
- [ ] T013 [P] `tools/smoke_org/files.py` y `tools/smoke_org/text_report.py`; `SmokeOrgError` y
      `EnvironmentFileError` en `model.py`.
- [ ] T014 `tools/smoke_org/environments/demo.json` y `tools/smoke_org/__main__.py`: argparse,
      logging, cableado, `print` del informe, código de salida.

## Phase 4: Validación y cierre

- [ ] T015 quickstart.md contra la demo: verde; fallo provocado y restaurado (`1`); sin datos (`2`).
      Cualquier forma de respuesta distinta de lo medido pasa a fixture.
- [ ] T016 Revisión contra el checklist de `AGENTS.md`; fila `tools/` en el `README.md` de la raíz;
      PR de `feat/001-smoke-org` a `main` con la spec enlazada y la salida de `smoke-org --env demo`;
      `tests / tests (3.11)` y `(3.12)` en verde. Tras el merge, `smoke-org` desde `main` y cierre del
      hito 0 en `CONTEXTO.md`.

---

## Dependencies & Execution Order

- Phase 1 sin dependencias; T002 en paralelo con T001.
- Phase 2: T004 y T005 antes que T006 y T007; T007 depende de T006.
- Phase 3: T008 a T011 en paralelo y antes que T012 y T013; T014 depende de T012 y T013.
- Phase 4 al final.
