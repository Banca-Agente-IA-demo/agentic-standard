# Implementation Plan: Clasificación del diff y salto de versión

**Branch**: `feat/008-diff-and-version` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

La tabla de las reglas de versión como código, con la fila que le faltaba: retirar capacidad es un
salto mayor. El diff se lee acotado a la carpeta de la unidad, se clasifica con datos, y de la
clasificación más la última versión publicada sale la propuesta. Calcular no escribe; sólo escribe
quien recibe la orden de aplicar, y sólo en el manifiesto de la unidad.

## Technical Context

**Language/Version**: Python 3.11 mínimo, el que declara `.python-version`.

**Primary Dependencies**: ninguna en el núcleo. `pytest` sólo para las pruebas.

**Storage**: el manifiesto de la unidad, que es donde vive la versión y el único archivo que se
escribe.

**Testing**: `pytest`. El dominio con datos; el caso de uso contra repositorios de verdad con el
proveedor de lanzamientos sustituido por un doble.

**Target Platform**: la máquina del autor, Windows incluido, y el runner de CI.

**Project Type**: núcleo del plugin de autoría más dos puntos de entrada.

**Constraints**: sólo biblioteca estándar; la suite corre sin red; el único destino de escritura está
bajo la raíz de la unidad elegida.

**Scale/Scope**: tres módulos de reglas, cuatro adaptadores, un caso de uso y dos puntos de entrada.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | El script decide el nivel mínimo y la versión que sale de él, que son hechos comprobables contra una tabla. El modelo presenta los motivos y recoge la elección. No interpreta el diff. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Sólo lectura: `diff --name-status`, `show` de un archivo de la rama principal y `rev-parse`. Ninguno que escriba. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | Nada nuevo de los clientes. Lo que sí se mide es el comportamiento de git al comparar contra la rama principal, y está fijado en pruebas. | Pasa |
| (4) Qué es dominio puro y qué adaptador | La tabla, la aritmética de la versión y la lectura de las etiquetas son puras. Leer el diff, preguntar por los lanzamientos, encontrar la unidad y escribir el manifiesto son adaptadores. | Pasa |
| (5) Qué nombres nuevos son contrato | Los tres niveles y los campos del documento que el diálogo consume. La forma de la etiqueta ya venía de las reglas de versión. | Pasa |
| (6) Qué escribe cada script y dónde | Sólo al aplicar, y sólo el manifiesto de la unidad. El destino se comprueba antes de escribir. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno. | Pasa |

## Decisiones, con su motivo

| Decisión | Motivo |
|---|---|
| Retirar un artefacto es mayor, y es una fila nueva | La tabla cubría añadir y cambiar, así que una eliminación caía por descarte en parche. Quien invoca un skill retirado se entera en ejecución. Anotado como supuesto en la spec, a confirmar con el usuario |
| Los renombrados no se detectan como tales | Con la detección activada, mover un artefacto sale como un cambio de texto, que es exactamente la vía para retirarlo de su sitio sin que se note. Partido en retirada y alta es lo que es para quien lo consume |
| El manifiesto no cuenta en la clasificación | Es donde vive la versión, así que cambia en todo salto. Contarlo haría que todo cambio fuera al menos parche por sí mismo |
| El gobierno se clasifica por claves, no por archivo | Cambiar el equipo dueño y cambiar los permisos son dos cosas muy distintas y viven en el mismo archivo |
| El único puerto es el de los lanzamientos | Es lo único que necesita red. Con doble, la suite corre sin salir de la máquina. Git, el manifiesto y la búsqueda de la unidad tienen implementación única y van sin puerto |
| Sin nada publicado, la versión se queda en la inicial | No hay a quien romperle nada todavía. Y si la principal ya iba por delante se respeta: retroceder el manifiesto sería peor que no moverlo |
| Se cuenta desde la mayor entre la actual y la publicada | Si alguien publicó desde otra rama, la principal va por detrás, y contar desde ella daría una versión que ya existe con otro contenido |
| El rechazo de un nivel insuficiente vive en quien escribe | Quien escribe es quien tiene que negarse. Dejarlo en el diálogo lo convierte en una convención que se cae en cuanto alguien llama al script directamente |

## Project Structure

### Documentation (this feature)

```text
specs/008-diff-and-version/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code

```text
plugins/authoring-assistant/
├── authoring_core/
│   ├── domain/
│   │   ├── diff_rules.py            la tabla, con la fila de la retirada
│   │   ├── versions.py              orden, precedencia y siguiente versión
│   │   └── release_tags.py          de las etiquetas a la última publicada
│   ├── ports/releases.py            el único puerto: quién sirve los lanzamientos
│   ├── application/version_planning.py  el caso de uso que consumen las dos entradas
│   └── adapters/
│       ├── diff.py                  el diff acotado a la unidad, sólo lectura
│       ├── releases.py              los lanzamientos, por la herramienta de GitHub
│       ├── units.py                 dónde vive una unidad, por su manifiesto
│       └── manifest.py              lee y escribe la versión, con el destino comprobado
├── skills/author-unit/scripts/
│   ├── diff_classify.py             qué salto exige el cambio, y por qué
│   └── version_bump.py              qué versión sale, y la escribe si se le pide
└── tests/
    ├── test_diff_rules.py           la tabla, fila por fila, con datos
    ├── test_version_rules.py        la aritmética de la versión, con datos
    ├── test_version_planning.py     el caso de uso, con repositorio y doble de lanzamientos
    └── test_version_scripts.py      los dos puntos de entrada
```

**Structure Decision**: la del plan del asistente. `ports/` estrena su único puerto y hay que vigilar
que siga siendo uno.

## Complexity Tracking

Sin violaciones que justificar. El módulo más largo tiene 160 líneas.
