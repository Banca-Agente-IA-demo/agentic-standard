# Implementation Plan: Estado de la unidad en su ciclo de vida

**Branch**: `feat/009-unit-state` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

El nodo de parada del camino de la obsolescencia: si la unidad no se ha publicado, no hay nada que
obsoletar. El estado se deriva de los lanzamientos, por el mismo puerto que estrenó la spec anterior,
y con una diferencia frente al comportamiento por omisión: una unidad cuyos lanzamientos están todos
en borrador no se da por en desarrollo, porque puede estar suspendida o retirada.

## Technical Context

**Language/Version**: Python 3.11 mínimo, el que declara `.python-version`.

**Primary Dependencies**: ninguna en el núcleo. `pytest` sólo para las pruebas.

**Storage**: ninguno. Esta capacidad no toca el repositorio del autor.

**Testing**: `pytest`, todo con datos. El puerto se sustituye con un doble.

**Target Platform**: la máquina del autor, Windows incluido, y el runner de CI.

**Project Type**: núcleo del plugin de autoría más un punto de entrada.

**Constraints**: sólo biblioteca estándar; sin red en la suite; ninguna escritura.

**Scale/Scope**: un módulo de reglas, un caso de uso y un punto de entrada.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | El script deriva el estado de lo publicado, que es un hecho. El modelo lo anuncia y decide si sigue por el camino de la obsolescencia. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. Es la única capacidad que no mira el repositorio del autor. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | Nada nuevo de los clientes. Lo que sí se fija en prueba es qué se responde cuando no se puede saber el estado. | Pasa |
| (4) Qué es dominio puro y qué adaptador | Derivar el estado es puro. Pedir los lanzamientos va por el puerto que ya existía. | Pasa |
| (5) Qué nombres nuevos son contrato | Los tres estados derivables ya eran contrato del lineamiento y están persistidos en el catálogo. El cuarto resultado es nuevo y a propósito no lleva ninguno de los seis nombres del ciclo de vida. | Pasa |
| (6) Qué escribe cada script y dónde | Nada. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno. | Pasa |

## Decisiones, con su motivo

| Decisión | Motivo |
|---|---|
| Una unidad con lanzamientos sólo en borrador no se da por en desarrollo | Suspender y retirar ponen los lanzamientos en borrador. Responder «en desarrollo: nada que obsoletar» a quien tiene una unidad suspendida es falso, y sus consumidores ya la tienen instalada |
| El resultado nuevo no lleva un nombre del ciclo de vida | Los seis estados son contrato persistido en el catálogo. Inventar un séptimo o reutilizar uno haría que un valor del catálogo significara dos cosas |
| Una beta por delante no saca a la unidad de producción | La transición de canal es de la unidad, no de la versión publicada. Se expone aparte que hay una versión en vuelo |
| Vive en su propio caso de uso | Derivar el estado del ciclo de vida y calcular un salto de versión son dos cosas, aunque las dos lean los lanzamientos |
| El módulo de reglas se llama igual que el punto de entrada | Es el nombre que fija el plan del asistente para el script, y el módulo dice exactamente lo mismo. La prueba del punto de entrada lo carga por su ruta y con otro nombre para que ninguno tape al otro |

## Project Structure

### Documentation (this feature)

```text
specs/009-unit-state/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code

```text
plugins/authoring-assistant/
├── authoring_core/
│   ├── domain/unit_state.py             el estado derivado de los lanzamientos
│   └── application/unit_lifecycle.py    el caso de uso
├── skills/author-unit/scripts/unit_state.py   el punto de entrada
└── tests/
    ├── test_unit_state_rules.py         los estados, con datos
    └── test_unit_state_script.py        el documento y el uso, sin red
```

**Structure Decision**: la del plan del asistente. `ports/` sigue con un solo puerto, ahora con dos
consumidores, que es exactamente lo que justificaba tenerlo.

## Complexity Tracking

Sin violaciones que justificar. El módulo de reglas tiene 85 líneas.
