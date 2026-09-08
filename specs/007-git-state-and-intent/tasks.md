# Tasks: El asistente sabe dónde está antes de proponer nada

**Input**: [plan.md](plan.md), [spec.md](spec.md)

Todas las tareas están hechas. Las rutas son relativas a la raíz del repositorio.

## Fase 1: Las reglas, con datos y sin repositorio

- [x] T001 Los seis estados y la forma del nombre de rama en
      `plugins/authoring-assistant/authoring_core/domain/git_state.py` (FR-001, FR-002, FR-004)
- [x] T002 El significado de una intención guardada en
      `plugins/authoring-assistant/authoring_core/domain/intent.py` (FR-008, FR-009)
- [x] T003 Las herramientas y la versión mínima del intérprete en
      `plugins/authoring-assistant/authoring_core/domain/tooling.py` (FR-010)
- [x] T004 [P] Pruebas de la clasificación en `plugins/authoring-assistant/tests/test_git_state_rules.py`
      (FR-013)
- [x] T005 [P] Pruebas de la interpretación en `plugins/authoring-assistant/tests/test_intent_rules.py`
      (FR-013)
- [x] T006 [P] Pruebas de la comprobación de herramientas en
      `plugins/authoring-assistant/tests/test_tooling_rules.py` (FR-013)

## Fase 2: Lo que habla con el exterior

- [x] T007 Lectura del repositorio, incluidos el atraso y los manifiestos, en
      `plugins/authoring-assistant/authoring_core/adapters/git.py` (FR-005, FR-006)
- [x] T008 La intención en la configuración local en
      `plugins/authoring-assistant/authoring_core/adapters/intent_store.py` (FR-007)
- [x] T009 Lo que la máquina tiene instalado en
      `plugins/authoring-assistant/authoring_core/adapters/tools.py` (FR-010)
- [x] T010 El orden de los tres pasos en
      `plugins/authoring-assistant/authoring_core/application/author_context.py`

## Fase 3: Los seis escenarios del banco de pruebas

- [x] T011 Los repositorios de prueba y sus seis escenarios, sin red, en
      `plugins/authoring-assistant/tests/repos.py`
- [x] T012 Cada escenario da su estado y clasificar no escribe nada, en
      `plugins/authoring-assistant/tests/test_git_adapter.py` (SC-001)
- [x] T013 La intención sobrevive, no ensucia el árbol y no viaja al clonar, en
      `plugins/authoring-assistant/tests/test_intent_store.py` (FR-007)

## Fase 4: Los puntos de entrada

- [x] T014 Lo común a los tres puntos de entrada en
      `plugins/authoring-assistant/skills/author-unit/scripts/_entry.py` (FR-011, FR-012, FR-014)
- [x] T015 [P] `preflight.py`
- [x] T016 [P] `git_state.py`
- [x] T017 [P] `intent.py`, con `get`, `set` y `clear`
- [x] T018 Un documento en la salida estándar, el diagnóstico en la de error y éxito en toda
      clasificación, en `plugins/authoring-assistant/tests/test_scripts.py` (FR-011, FR-012)

## Fase 5: Cierre

- [x] T019 La suite completa del plugin en verde en local
- [x] T020 CI en verde en las dos versiones del intérprete
- [x] T021 `CONTEXTO.md` actualizado con lo decidido y lo medido

## Dependencias

La fase 1 no depende de nada. La 2 depende de la 1. La 3 depende de la 2. La 4 depende de la 2. Las
tareas marcadas [P] tocan archivos distintos y pueden ir a la vez.
