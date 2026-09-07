# Tasks: Prueba de humo de la organización

**Input**: Design documents from `/specs/001-smoke-org/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: obligatorias. La constitución (principio IV, reglas T1 a T6 de `AGENTS.md`) exige dominio
probado con datos, adaptadores con dobles inyectados y una prueba de regresión por cada medición. Las
pruebas se escriben antes que el código que cubren y deben fallar primero.

**Organization**: tareas agrupadas por historia de usuario para que cada una se implemente y pruebe
de forma independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ir en paralelo (archivos distintos, sin dependencias)
- **[Story]**: historia a la que pertenece (US1, US2, US3)
- Cada tarea nombra los archivos exactos

## Path Conventions

Componente `tools/smoke_org/` con capas `domain/`, `application/`, `ports/`, `adapters/`; pruebas en
`tests/smoke_org/` con la misma división. Rutas relativas a la raíz de `agentic-standard`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: paquete instalable, pruebas ejecutables y CI antes de escribir una sola regla.

- [ ] T001 Crear `pyproject.toml` en la raíz: `[project]` con `name = "agentic-standard-tools"`,
      `requires-python = ">=3.11"`, sin dependencias de ejecución, `optional-dependencies.dev = ["pytest"]`;
      `[project.scripts] smoke-org = "smoke_org.__main__:main"`; `[tool.setuptools.packages.find]
      where = ["tools"]`; `[tool.pytest.ini_options] testpaths = ["tests"]`.
- [ ] T002 Crear el esqueleto del paquete con `__init__.py` vacíos: `tools/smoke_org/`,
      `tools/smoke_org/domain/`, `tools/smoke_org/application/`, `tools/smoke_org/ports/`,
      `tools/smoke_org/adapters/`, `tools/smoke_org/environments/`, y `tests/smoke_org/` con
      `domain/`, `application/`, `adapters/`, `adapters/fixtures/`.
- [ ] T003 [P] Crear `.github/workflows/tests.yml`: `on: pull_request` a `main` con `paths`
      `tools/**`, `tests/**`, `config/teams.json`, `pyproject.toml`, `.github/workflows/tests.yml`;
      `permissions: contents: read`; un job `tests` con `strategy.matrix.python-version: ["3.11", "3.12"]`;
      `actions/checkout` y `actions/setup-python` por SHA con comentario de versión; pasos
      `python -m pip install -e ".[dev]"` y `python -m pytest -q`. Cabecera con el propósito. Menos de
      150 líneas.
- [ ] T004 [P] Añadir a `.gitignore` de la raíz lo que genere la instalación editable si falta
      (`*.egg-info/` ya está; comprobar `build/`).
- [ ] T005 Verificar localmente: `python -m pip install -e ".[dev]"` y `python -m pytest -q` en verde
      con cero pruebas recogidas; `smoke-org --help` responde.

**Checkpoint**: el repo instala, `pytest` corre y el workflow existe.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: los tipos del dominio, el puerto y el caso de uso vacío que toda comprobación necesita.

**⚠️ CRITICAL**: ninguna historia empieza hasta cerrar esta fase.

- [ ] T006 [P] `tools/smoke_org/domain/contract.py`: constantes de data-model.md sección Contract
      (`APP_SLUG`, `APP_SECRET_NAMES`, `MARKETPLACE_VARIABLE_NAMES`, `DOMAIN_TOPIC`,
      `MAIN_RULESET_NAME`, `TAGS_RULESET_NAME`, `REQUIRED_CONTEXTS`, `ACTIONS_INTEGRATION_ID`).
      Docstring que dice que son contrato y remite a la guía.
- [ ] T007 [P] `tools/smoke_org/domain/report.py`: `CheckStatus`, `CheckResult`, `Report`,
      `Verdict` con su código de salida, y la función pura `verdict_of(report) -> Verdict` con la
      regla «UNCHECKED prevalece sobre FAIL».
- [ ] T008 [P] `tests/smoke_org/domain/test_report.py`: `test_sin_resultados_fallidos_ni_sin_datos_pasa`,
      `test_un_fallo_basta_para_no_pasar`, `test_sin_datos_prevalece_sobre_fallo`,
      `test_cada_veredicto_tiene_su_codigo_de_salida` (bucle sobre los tres, T5).
- [ ] T009 [P] `tools/smoke_org/domain/environment.py`: `IndexChannel`, `Marketplace`, `Environment`,
      `TeamRoster` y la función pura `validate_environment(env) -> tuple[str, ...]` con las reglas de
      data-model.md (organización no vacía, al menos un marketplace, canales distintos, sin repos
      repetidos entre listas).
- [ ] T010 [P] `tests/smoke_org/domain/test_environment.py`: una prueba por regla de validación con
      el nombre del defecto (`test_dos_marketplaces_con_el_mismo_canal_es_error`, etc.).
- [ ] T011 `tools/smoke_org/ports/github_reader.py`: `Unavailable`, alias `Observed[T]`,
      `OrganizationSettings`, `AppInstallation`, `RequiredContext`, `Ruleset`, `OrganizationSnapshot`
      y el `Protocol GitHubReader` con un método por pieza observada (depende de T006 para los tipos de
      enforcement/target como `Enum`).
- [ ] T012 `tools/smoke_org/application/run_smoke.py`: `run_smoke(environment, roster, reader) -> Report`
      que construye el snapshot llamando al puerto y recorre una lista `CHECKS` (vacía en esta tarea)
      sin cortar en el primer fallo. Depende de T007, T009, T011.
- [ ] T013 `tests/smoke_org/application/fake_reader.py`: `FakeGitHubReader` construido a partir de
      un `OrganizationSnapshot` dado; y `tests/smoke_org/application/test_run_smoke.py` con
      `test_recorre_todas_las_comprobaciones_aunque_la_primera_falle` (T4, inyección sin monkeypatch).
- [ ] T014 `tools/smoke_org/adapters/environment_loader.py`: `load_environment(path) -> Environment`
      y `load_team_roster(path) -> TeamRoster`; una clave desconocida en el JSON de entorno es un
      `EnvironmentFileError` (jerarquía `SmokeOrgError` en `tools/smoke_org/domain/errors.py`).
- [ ] T015 `tests/smoke_org/adapters/test_environment_loader.py` con `tmp_path`:
      `test_clave_desconocida_en_el_entorno_es_error`, `test_json_invalido_es_error`,
      `test_el_roster_recorre_todos_los_papeles_de_teams_json` (usa el `config/teams.json` real del
      repo como fixture, porque FR-002 exige leer ese archivo).
- [ ] T016 `tools/smoke_org/environments/demo.json` con los valores del contrato cli.md, y
      `tools/smoke_org/__main__.py`: `argparse` con `--env`, `--environments-dir`, `--teams-file`,
      `--verbose`; `_configure_logging` (L4, L9); cableado de `GhCliReader` (stub hasta la fase 3);
      `main()` que traduce `SmokeOrgError` a código `2` y `Verdict` a su código. Sin lógica de negocio.

**Checkpoint**: `smoke-org --env demo` arranca, no comprueba nada y sale con `0`; `pytest` verde.

---

## Phase 3: User Story 1 - Veredicto de la organización en una ejecución (Priority: P1) 🎯 MVP

**Goal**: todas las comprobaciones de la guía §10 salvo las de rulesets, el informe legible y los
tres códigos de salida, contra la organización real.

**Independent Test**: `smoke-org --env demo` en verde; retirar una variable de un marketplace y
obtener `[FALLA]` con esperado y encontrado y código `1`; sin `admin:org`, `[SIN DATOS]` y código `2`.

### Tests for User Story 1

- [ ] T017 [P] [US1] `tests/smoke_org/domain/test_checks_org_settings.py`: pasa con valores iguales;
      falla por cada uno de los tres campos en bucle con el campo en el mensaje; `UNCHECKED` si el
      snapshot trae `Unavailable`.
- [ ] T018 [P] [US1] `tests/smoke_org/domain/test_checks_teams.py`: un resultado por slug del roster;
      el que falta sale `FAILED` con el slug como ámbito; equipos extra no fallan.
- [ ] T019 [P] [US1] `tests/smoke_org/domain/test_checks_app.py`: sin instalación falla; `all` pasa;
      `selected` que cubre todos los repos esperados pasa; `selected` que omite uno falla nombrándolo;
      otra App con `all` no cuenta.
- [ ] T020 [P] [US1] `tests/smoke_org/domain/test_checks_secrets.py`: cada repo esperado con los dos
      nombres pasa; un nombre con distinta caja o guion cuenta como ausente; repo sin datos sale
      `UNCHECKED` sólo para ese repo.
- [ ] T021 [P] [US1] `tests/smoke_org/domain/test_checks_variables.py`: las dos variables presentes y
      `INDEX_CHANNEL` igual al canal pasa; canal cruzado falla con esperado y encontrado; variable
      ausente falla con «encontrado ausente».
- [ ] T022 [P] [US1] `tests/smoke_org/domain/test_checks_topic.py`: todos los dominios con topic
      pasa; un dominio sin topic falla; un repo no dominio con topic falla nombrándolo.
- [ ] T023 [P] [US1] `tests/smoke_org/adapters/fixtures/`: guardar las respuestas reales medidas el
      2026-09-07 (research.md R6): `org.json`, `teams.json`, `installations_all.json`,
      `secret_list.json`, `variable_list.json`, `repo_list_topic.json`, y los dos errores
      `gh_no_session.txt` (código 4) y `gh_forbidden.json` (código 1). Cada archivo con un
      `README.md` de la carpeta que dice comando, fecha y organización de origen (T3).
- [ ] T024 [US1] `tests/smoke_org/adapters/test_gh_cli_reader.py`: `FakeCommandRunner` que devuelve
      `(returncode, stdout, stderr)` por comando; una prueba por método del lector que parsea su
      fixture; `test_sin_sesion_de_gh_devuelve_unavailable_con_el_mensaje`,
      `test_403_devuelve_unavailable_sin_lanzar`; `test_el_comando_se_construye_como_lista` (P10).
- [ ] T025 [P] [US1] `tests/smoke_org/adapters/test_text_report.py`: una línea por resultado con la
      etiqueta entre corchetes; esperado y encontrado con esas palabras; resumen con los tres
      contadores; veredicto en la última línea con los tres textos del contrato.

### Implementation for User Story 1

- [ ] T026 [P] [US1] `tools/smoke_org/domain/checks.py`: `check_org_settings`, `check_teams`,
      `check_app_installed`, `check_secrets`, `check_variables`, `check_topic`, cada una pura con la
      firma de data-model.md y devolviendo `UNCHECKED` ante `Unavailable`; registrar en `CHECKS`.
- [ ] T027 [US1] `tools/smoke_org/adapters/gh_cli_reader.py`: `CommandRunner` como `Protocol` con
      default `subprocess.run` inyectable; `GhCliReader(organization, runner=...)` que implementa el
      puerto con los comandos de research.md R6 construidos como listas, `--json` siempre, paginación
      con `--paginate` donde aplique; traduce código distinto de 0 a `Unavailable(reason)` con el
      mensaje de `stderr` o del JSON. Logging `DEBUG` por comando con duración (L3, L7).
- [ ] T028 [P] [US1] `tools/smoke_org/adapters/text_report.py`: `render_text(report) -> str` según
      el formato de contracts/cli.md.
- [ ] T029 [US1] `tools/smoke_org/__main__.py`: cablear `GhCliReader` real, `render_text` a `stdout`
      con `print`, y el código de salida del veredicto. Depende de T027, T028.
- [ ] T030 [US1] Ejecutar quickstart.md contra la demo: verde, fallo provocado y restaurado, y el
      escenario sin datos. Anotar en `research.md` cualquier forma de respuesta que difiera de lo
      medido y convertirla en fixture.

**Checkpoint**: la historia 1 es un MVP utilizable; sólo faltan los rulesets.

---

## Phase 4: User Story 2 - Los tres requeridos del ruleset son exactos (Priority: P1)

**Goal**: comprobar los dos rulesets por nombre y modo, y los tres contextos exactos con su origen.

**Independent Test**: contra `agents-modernization` pasa; con un ruleset renombrado, desactivado, o
con un contexto de menos, de más o mal escrito, falla mostrando esperados frente a encontrados.

### Tests for User Story 2

- [ ] T031 [P] [US2] `tests/smoke_org/domain/test_checks_rulesets_present.py`: ambos activos pasa;
      falta uno falla nombrándolo; presente pero `evaluate` o `disabled` falla; nombre distinto no
      cuenta aunque tenga las mismas reglas.
- [ ] T032 [P] [US2] `tests/smoke_org/domain/test_checks_rulesets_contexts.py`: los tres exactos con
      `15368` pasa; en bucle: uno de menos, uno de más, uno con un carácter distinto, uno con otro
      `integration_id`; cada caso falla y el detalle muestra esperados y encontrados.
- [ ] T033 [P] [US2] Fixtures reales: `rulesets_list.json` y `ruleset_protect_main.json`,
      `ruleset_protect_tags.json` medidos el 2026-09-07 en `agents-modernization`, con su entrada en
      el `README.md` de fixtures.
- [ ] T034 [US2] Ampliar `test_gh_cli_reader.py`: parseo de la lista y del detalle de cada ruleset;
      la lista no trae reglas y el lector pide cada `id` (`test_pide_el_detalle_de_cada_ruleset`).

### Implementation for User Story 2

- [ ] T035 [US2] `checks.py`: `check_rulesets_present` y `check_rulesets_contexts`; añadir a `CHECKS`
      en el orden de data-model.md.
- [ ] T036 [US2] `gh_cli_reader.py`: `rulesets_for(repository)` con las dos llamadas y el parseo de
      `required_status_checks`.
- [ ] T037 [US2] Ejecutar contra la demo y validar el escenario 2 de la historia (editar a mano un
      contexto en un ruleset de prueba, o en `agents-modernization` con reversión inmediata, y ver el
      fallo). Anotar dónde se midió.

**Checkpoint**: las dos historias P1 completas; SC-002 cumplido (las diez comprobaciones de §10).

---

## Phase 5: User Story 3 - La misma prueba sirve para la demo y para BCP (Priority: P2)

**Goal**: cambiar de entorno cambia sólo valores, nunca comprobaciones.

**Independent Test**: con un entorno que declare otro plan y otro permiso base contra la misma
organización, fallan exactamente `org.settings` y nada más.

### Tests for User Story 3

- [ ] T038 [P] [US3] `tests/smoke_org/application/test_environment_switch.py`: mismo snapshot falso,
      dos entornos que difieren sólo en plan y permiso base; el conjunto de `check_id` es idéntico y
      sólo `org.settings` cambia de estado.
- [ ] T039 [P] [US3] `tests/smoke_org/adapters/test_environment_files.py`: `demo.json` y `bcp.json`
      cargan y validan; `bcp.json` declara `plan = enterprise` y `default_repository_permission = none`.

### Implementation for User Story 3

- [ ] T040 [US3] `tools/smoke_org/environments/bcp.json`: plantilla con los valores de la guía §11
      para BCP y marcadores claros en organización y nombres de repos (`"TODO-BCP"`) que la validación
      rechaza hasta que se rellenen, con un comentario `$comment` que lo explique.
- [ ] T041 [US3] `README.md` del componente `tools/smoke_org/README.md`: qué comprueba, cómo se
      ejecuta, cómo se añade un entorno, qué hay que pedir en BCP (sesión `gh` con `read:org`).

**Checkpoint**: las tres historias completas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T042 [P] Revisar cada módulo contra el checklist de `AGENTS.md`: imports arriba, sin
      `except Exception` fuera de `main()`, sin `SystemExit` fuera de `main()`, `log = logging.getLogger(__name__)`,
      `%s` en logs, constantes nombradas para el límite de `--limit 1000` (P11), ningún módulo sobre
      300 líneas.
- [ ] T043 [P] Actualizar `README.md` de la raíz del estándar: fila para `tools/` y el comando
      `smoke-org` en «Cómo se trabaja aquí».
- [ ] T044 Abrir el PR de `feat/001-smoke-org` a `main` con la spec enlazada, el Constitution Check
      del plan y la salida de `smoke-org --env demo` como evidencia; comprobar que `tests / tests (3.11)`
      y `tests / tests (3.12)` corren en verde.
- [ ] T045 Tras el merge: ejecutar `smoke-org --env demo` desde `main` y registrar en `CONTEXTO.md`
      del espacio de trabajo el cierre del hito 0 con la fecha.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; bloquea todas las historias.
- **US1 (Phase 3)** y **US2 (Phase 4)**: dependen de Foundational. US2 reutiliza el lector y el
  informe de US1 (T027, T028), así que en la práctica va después de T029.
- **US3 (Phase 5)**: depende de Foundational; independiente de US1 y US2 salvo por la lista `CHECKS`.
- **Polish (Phase 6)**: depende de las tres historias.

### Within Each User Story

- Las pruebas del dominio (T1) van antes que `checks.py`; las del adaptador antes que el lector.
- Fixtures antes que las pruebas del lector que las consumen.
- Dominio antes que caso de uso; caso de uso antes que `__main__.py`.

### Parallel Opportunities

- Phase 1: T003 y T004 en paralelo con T001 y T002.
- Phase 2: T006, T007, T008, T009, T010 en paralelo; T011 después de T006; T012 después de T007,
  T009, T011.
- Phase 3: T017 a T023 y T025 en paralelo; T026 y T028 en paralelo; T027 después de T023 y T024.
- Phase 4: T031, T032, T033 en paralelo.

---

## Parallel Example: User Story 1

```text
# Pruebas del dominio, todas a la vez (archivos distintos):
T017 test_checks_org_settings.py
T018 test_checks_teams.py
T019 test_checks_app.py
T020 test_checks_secrets.py
T021 test_checks_variables.py
T022 test_checks_topic.py

# Después, implementación en paralelo:
T026 domain/checks.py
T028 adapters/text_report.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 y Phase 2.
2. Phase 3 completa: ya sirve para cerrar el hito 0 salvo por los rulesets.
3. Validar con quickstart.md contra la demo.

### Incremental Delivery

1. US1: veredicto sin rulesets.
2. US2: rulesets y contextos; con esto la lista de la guía §10 queda cubierta (SC-002).
3. US3: `bcp.json` y la prueba de que cambiar de entorno no cambia comprobaciones (SC-005).
4. Polish y PR.

---

## Notes

- 45 tareas. Ninguna spec cubre más de dos scripts o un camino del árbol (constitución); aquí hay un
  solo comando.
- Cada fixture lleva comando, fecha y organización de origen (T3).
- Los nombres de las pruebas son prosa en español que nombra el defecto (T2); los identificadores
  del código, en inglés (G3b).
- Commit por tarea o grupo lógico; la rama es `feat/001-smoke-org`.
