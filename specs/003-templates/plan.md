# Implementation Plan: Plantillas de unidad y de artefacto

**Branch**: `feat/003-templates` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Copiar sin modificación `templates/` del paquete de diseño del hito 1 y convertir a `pytest` las tres
comprobaciones de plantillas de su `selfcheck.py`, más una nueva sobre la lista de eventos portables
de D3. Sin código de producción: el entregable son las plantillas y sus pruebas.

## Technical Context

**Language/Version**: Python 3.11 mínimo, matriz 3.11 y 3.12 en CI.

**Primary Dependencies**: `jsonschema` (ya está desde la spec 002) y `pyyaml`, ambas de
**desarrollo**. `pyyaml` hace falta para leer el frontmatter de las plantillas de texto y la suite.

**Storage**: archivos bajo `templates/`, leídos por ruta desde las pruebas.

**Testing**: `pytest`. Sin red y sin dobles; el único disco es la lectura de las plantillas.

**Target Platform**: la máquina del equipo y el runner de CI.

**Project Type**: material de plantilla con su suite de pruebas.

**Constraints**: las plantillas se copian **byte a byte**; se editan primero en el paquete de diseño.
`.gitattributes` ya fija finales de línea para `templates/`, así que un clon nuevo sigue coincidiendo.

**Scale/Scope**: dieciséis archivos de plantilla, unas veinte comprobaciones.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | No hay modelo. Las pruebas comprueban archivos. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | La lista de eventos portables está medida en los dos clientes (D3) y se convierte en la prueba de eventos de la plantilla de hooks (T3). | Pasa |
| (4) Qué es dominio puro y qué adaptador | Todo es dominio: datos y aserciones. | Pasa |
| (5) Qué nombres nuevos son contrato | Los marcadores de plantilla y la lista de eventos portables. Ninguno se renombra. | Pasa |
| (6) Qué escribe cada script y dónde | Nada. La instanciación ocurre en memoria. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno nuevo. Se amplían las rutas del workflow de pruebas para cubrir `templates/`. | Pasa |

## Project Structure

### Documentation (this feature)

```text
specs/003-templates/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
templates/                          copiado tal cual del paquete de diseño
├── plugin-unit/          .claude-plugin/plugin.json, GOVERNANCE.json, README.md
├── individual-unit/      lo mismo para un artefacto solo
└── artifacts/            skill, agent, prompt, hooks, mcp, evals

tests/templates/
├── __init__.py
├── markers.py                      valores de prueba de cada marcador e instanciación
├── test_unit_templates.py          historia 1
└── test_artifact_templates.py      historias 2 y 3
```

**Structure Decision**: `templates/` ya existía vacío en el árbol del lineamiento 02 §3.4. Las pruebas
van bajo `tests/templates/`. Los valores de prueba y la función que sustituye marcadores viven en su
propio módulo porque los usan los dos archivos de prueba, y el asistente de autoría del hito 2 puede
partir de esa misma lista de marcadores.

## Complexity Tracking

Sin violaciones que justificar.
