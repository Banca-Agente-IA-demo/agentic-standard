# Implementation Plan: Prueba de humo de la organización

**Branch**: `feat/001-smoke-org` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-smoke-org/spec.md`

## Summary

Una herramienta de línea de comandos, `smoke-org`, que consulta la organización de GitHub a través
de la sesión autenticada de `gh` y compara lo que encuentra con un archivo de valores esperados por
entorno (demo, BCP). Ejecuta todas las comprobaciones de la guía §10, imprime un informe legible con
tres resultados posibles por comprobación y termina con uno de tres códigos de salida. El dominio
(qué se compara y cómo se decide el resultado) es puro y se prueba con datos; el único adaptador con
I/O externa es el lector de GitHub, detrás de un puerto con un doble para las pruebas.

## Technical Context

**Language/Version**: Python 3.11 como mínimo declarado (`requires-python = ">=3.11"`); desarrollo con
3.12; CI con matriz 3.11 y 3.12. Decidido el 2026-09-07: el suelo protege al asistente de autoría,
que corre en máquinas de BCP cuyo Python no se ha medido (hito A0).

**Primary Dependencies**: sólo biblioteca estándar en tiempo de ejecución (`subprocess`, `json`,
`argparse`, `logging`, `dataclasses`, `enum`, `pathlib`). `gh` CLI autenticado como dependencia
externa de ejecución. `pytest` como única dependencia de desarrollo.

**Storage**: ninguno. Lee `config/teams.json` del repositorio y un archivo de entorno esperado
`tools/smoke_org/environments/<entorno>.json`.

**Testing**: `pytest`. Dominio con datos, sin disco ni red (T1). Adaptador de `gh` con un doble
inyectado (T4). Cada forma de respuesta medida contra la organización real se convierte en fixture
con el comentario de dónde se midió (T3).

**Target Platform**: máquina de una persona del equipo de plataforma, Windows con PowerShell o Git
Bash, y Linux en CI. Sin ejecución programada en GitHub (ver Assumptions de la spec).

**Project Type**: herramienta CLI, componente `tools/smoke_org/` dentro del repositorio del estándar.

**Performance Goals**: veredicto en menos de un minuto (SC-001). Del orden de 25 llamadas a `gh`
para la organización de demo; cada una tarda menos de dos segundos. Sin paralelismo.

**Constraints**: sólo lectura sobre GitHub (FR-015). No lee variables de entorno de credenciales ni
archivos de secretos: la autenticación es la de `gh` (constitución VI). Sin em-dashes.

**Scale/Scope**: una organización, cuatro repositorios en la demo; en BCP, decenas de repositorios de
dominio como máximo. El recorrido es lineal por repositorio.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | Todo lo decide el código; no hay modelo en esta capacidad. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. La herramienta no toca git ni el repositorio del autor; sólo lee `config/teams.json` del propio estándar. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | No depende de Copilot ni de Claude Code. Se mide la forma de las respuestas de `gh` contra la organización de demo y cada forma es una fixture con su origen anotado (T3). | Pasa |
| (4) Qué es dominio puro y qué adaptador | Dominio: contrato de nombres, entorno esperado, comprobaciones, informe y veredicto; sin `subprocess` ni `pathlib`. Adaptadores: lector de GitHub vía `gh` y carga de JSON de disco. Un puerto, `GitHubReader`, con dos implementaciones reales (gh y doble de test). | Pasa |
| (5) Qué nombres nuevos son contrato | `protect-main` y `protect-tags` pasan a contrato (clarify). Los códigos de salida 0, 1, 2 y el nombre del comando `smoke-org` son interfaz pública de esta herramienta. Ningún nombre existente se renombra. | Pasa |
| (6) Qué escribe cada script y dónde | Nada. Sólo `stdout` (informe) y `stderr` (logging). | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Un workflow `tests.yml` con un solo evento (`pull_request` a `main`, filtrado por rutas) y un solo job `tests` con matriz de versiones de Python. Sin secretos, `permissions: contents: read`. | Pasa |

Re-evaluación tras la fase 1: sin cambios. No hay entradas en Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-smoke-org/
├── input.md             # Texto de entrada de specify
├── spec.md              # Especificación con las aclaraciones integradas
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones técnicas con alternativas
├── data-model.md        # Fase 1: entidades del dominio
├── quickstart.md        # Fase 1: cómo ejecutar y validar
├── contracts/
│   └── cli.md           # Fase 1: contrato del comando (argumentos, salida, códigos)
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2: lo genera /speckit-tasks
```

### Source Code (repository root)

Revisado el 2026-09-07: versión reducida. La herramienta traduce diez comandos `gh` a un veredicto;
no justifica paquetes por capa ni un puerto formal. Se conserva la separación que importa (dominio
puro con datos, adaptador de `gh` con runner inyectable) en módulos planos.

```text
pyproject.toml                       # paquete smoke_org bajo tools/, script smoke-org, pytest
.github/workflows/tests.yml          # pull_request a main: pytest en 3.11 y 3.12

tools/
└── smoke_org/
    ├── __init__.py
    ├── __main__.py                  # entry point: argparse, logging, cableado, exit code
    ├── model.py                     # dominio: nombres contrato, Environment, snapshot, resultados, veredicto
    ├── checks.py                    # dominio: las ocho comprobaciones puras y la lista CHECKS
    ├── gh_reader.py                 # adaptador: gh en subprocess con CommandRunner inyectable
    ├── files.py                     # adaptador: carga de environments/<n>.json y config/teams.json
    ├── text_report.py               # adaptador: Report a texto
    └── environments/
        └── demo.json

tests/
└── smoke_org/
    ├── fixtures/                    # respuestas reales de gh medidas el 2026-09-07, con README
    ├── test_model.py                # veredicto y validación del entorno (T1)
    ├── test_checks.py               # cada comprobación con datos (T1)
    ├── test_gh_reader.py            # parseo de fixtures con runner falso (T4)
    ├── test_files.py                # carga de JSON con tmp_path
    └── test_text_report.py
```

**Structure Decision**: componente único bajo `tools/`, porque el árbol del lineamiento 02 §3.4 no
reserva sitio a herramientas de plataforma. Módulos planos en vez de paquetes por capa: la constitución
IV pide dominio puro y adaptadores sustituibles, y eso se cumple con `model.py` y `checks.py` sin
`subprocess` ni `pathlib`, y con `gh_reader.py` recibiendo el runner por parámetro. Un puerto formal
tendría una sola implementación real, lo que `AGENTS.md` G5 desaconseja. `bcp.json` se difiere al
hito 8 junto con la historia 3.

## Complexity Tracking

Sin violaciones que justificar.
