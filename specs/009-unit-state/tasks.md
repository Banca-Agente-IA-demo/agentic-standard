# Tasks: Estado de la unidad en su ciclo de vida

**Input**: [plan.md](plan.md), [spec.md](spec.md)

Todas las tareas están hechas. Las rutas son relativas a la raíz del repositorio.

## Fase 1: Las reglas, con datos

- [x] T001 El estado derivado de los lanzamientos en
      `plugins/authoring-assistant/authoring_core/domain/unit_state.py` (FR-001 a FR-009)
- [x] T002 Pruebas de cada estado, incluido el que no se afirma, en
      `plugins/authoring-assistant/tests/test_unit_state_rules.py` (SC-001, FR-010)

## Fase 2: El caso de uso y el punto de entrada

- [x] T003 El caso de uso en `plugins/authoring-assistant/authoring_core/application/unit_lifecycle.py`
      (FR-011)
- [x] T004 El punto de entrada en `plugins/authoring-assistant/skills/author-unit/scripts/unit_state.py`
- [x] T005 Pruebas del documento y del uso, sin red, en
      `plugins/authoring-assistant/tests/test_unit_state_script.py` (SC-002)

## Fase 3: Cierre

- [x] T006 La suite completa en verde en local y el validador sin hallazgos nuevos sobre la unidad
- [x] T007 CI en verde en las dos versiones del intérprete
- [x] T008 `CONTEXTO.md` actualizado, con el hito A1 cerrado y lo que queda abierto

## Dependencias

La fase 2 depende de la 1. La 3, de las dos.
