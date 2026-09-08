# Tasks: Clasificación del diff y salto de versión

**Input**: [plan.md](plan.md), [spec.md](spec.md)

Todas las tareas están hechas. Las rutas son relativas a la raíz del repositorio.

## Fase 1: Las reglas, con datos

- [x] T001 La tabla, con la fila de la retirada, en
      `plugins/authoring-assistant/authoring_core/domain/diff_rules.py` (FR-002 a FR-006)
- [x] T002 Orden, precedencia y siguiente versión en
      `plugins/authoring-assistant/authoring_core/domain/versions.py` (FR-007, FR-009 a FR-011)
- [x] T003 De las etiquetas a la última publicada en
      `plugins/authoring-assistant/authoring_core/domain/release_tags.py` (FR-008)
- [x] T004 [P] Pruebas de la tabla en `plugins/authoring-assistant/tests/test_diff_rules.py` (SC-001)
- [x] T005 [P] Pruebas de la versión en `plugins/authoring-assistant/tests/test_version_rules.py`
      (SC-004)

## Fase 2: El puerto y lo que habla con el exterior

- [x] T006 El único puerto en `plugins/authoring-assistant/authoring_core/ports/releases.py` (FR-016)
- [x] T007 El diff acotado a la unidad en
      `plugins/authoring-assistant/authoring_core/adapters/diff.py` (FR-001)
- [x] T008 Los lanzamientos por la herramienta de GitHub en
      `plugins/authoring-assistant/authoring_core/adapters/releases.py`
- [x] T009 Dónde vive una unidad, por su manifiesto, en
      `plugins/authoring-assistant/authoring_core/adapters/units.py`
- [x] T010 Lectura y escritura de la versión, con el destino comprobado, en
      `plugins/authoring-assistant/authoring_core/adapters/manifest.py` (FR-013)
- [x] T011 El caso de uso único en
      `plugins/authoring-assistant/authoring_core/application/version_planning.py` (FR-014)

## Fase 3: Contra un repositorio de verdad

- [x] T012 Una unidad de prueba con un artefacto ya publicado y su gobierno, en
      `plugins/authoring-assistant/tests/repos.py`
- [x] T013 El caso de uso completo con el doble de lanzamientos, en
      `plugins/authoring-assistant/tests/test_version_planning.py` (SC-002, SC-003)

## Fase 4: Los puntos de entrada

- [x] T014 [P] `diff_classify.py`
- [x] T015 [P] `version_bump.py`, con y sin la orden de aplicar (FR-012)
- [x] T016 Pruebas de los dos en `plugins/authoring-assistant/tests/test_version_scripts.py`

## Fase 5: Cierre

- [x] T017 La suite completa en verde en local y el validador sin hallazgos nuevos sobre la unidad
- [x] T018 CI en verde en las dos versiones del intérprete
- [x] T019 `CONTEXTO.md` actualizado con lo decidido y lo medido

## Dependencias

La fase 1 no depende de nada. La 2 depende de la 1. Las fases 3 y 4 dependen de la 2. Las tareas
marcadas [P] tocan archivos distintos y pueden ir a la vez.
