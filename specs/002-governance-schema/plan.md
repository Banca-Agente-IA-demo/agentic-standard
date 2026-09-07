# Implementation Plan: Esquemas de gobierno y de marketplace

**Branch**: `feat/002-governance-schema` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Copiar sin modificación los dos esquemas del paquete de diseño del hito 1 a `schemas/`, y convertir a
`pytest` las comprobaciones de `check_governance` y `check_marketplace` de su `selfcheck.py`, con
nombres que digan el defecto. No hay código de producción: el entregable es un contrato y sus pruebas.

## Technical Context

**Language/Version**: Python 3.11 mínimo, matriz 3.11 y 3.12 en CI, como fijó el hito 0.

**Primary Dependencies**: `jsonschema` como dependencia de **desarrollo**. No hay dependencias de
ejecución: los esquemas son datos. El paquete del validador declarará la suya en `std-003`.

**Storage**: dos archivos JSON en `schemas/`, leídos por ruta desde las pruebas.

**Testing**: `pytest`. Todo con datos en memoria; sin disco fuera de la lectura de los esquemas y las
fixtures, sin red, sin dobles.

**Target Platform**: la máquina del equipo y el runner de CI.

**Project Type**: contrato de datos con su suite de pruebas.

**Constraints**: los esquemas se copian **byte a byte**. Cualquier corrección se hace primero en el
paquete de diseño, se comprueba con su `selfcheck.py` y se vuelve a copiar; el repositorio no es el
sitio donde se editan por primera vez.

**Scale/Scope**: dos esquemas, cuatro fixtures, unas treinta comprobaciones.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | No hay modelo. El esquema decide; la prueba comprueba. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | La divergencia entre clientes ya está medida (Copilot rechaza `git-subdir`, Claude ignora `path`) y se convierte en las pruebas de proyección cruzada (T3). | Pasa |
| (4) Qué es dominio puro y qué adaptador | Todo es dominio: datos y aserciones. Sin adaptadores. | Pasa |
| (5) Qué nombres nuevos son contrato | Todos los identificadores del esquema, ya listados en el README del paquete de diseño. No se renombra ninguno. | Pasa |
| (6) Qué escribe cada script y dónde | Nada. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno nuevo. Se amplían las rutas del workflow de pruebas existente para que cubra `schemas/`. | Pasa |

## Project Structure

### Documentation (this feature)

```text
specs/002-governance-schema/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
schemas/
├── governance.schema.json          copiado tal cual del paquete de diseño
└── marketplace.schema.json         copiado tal cual del paquete de diseño

tests/schemas/
├── conftest.py                     carga de esquemas, validadores y helper de errores
├── fixtures/
│   ├── governance-plugin-with-mcp.json
│   ├── governance-individual-deprecated.json
│   ├── marketplace-exp.claude-code.json
│   ├── marketplace-exp.copilot.json
│   └── README.md                   procedencia de cada fixture
├── test_governance_schema.py
└── test_marketplace_schema.py
```

**Structure Decision**: `schemas/` ya existía vacío en el árbol del lineamiento 02 §3.4; esta spec lo
llena. Las pruebas van bajo `tests/schemas/` para que `tests/smoke_org/` siga siendo el del hito 0. El
`conftest.py` concentra la construcción de los validadores, que es lo único repetido entre los dos
archivos de prueba.

## Complexity Tracking

Sin violaciones que justificar.
