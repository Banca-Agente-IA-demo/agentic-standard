# Implementation Plan: El asistente sabe dónde está antes de proponer nada

**Branch**: `feat/007-git-state-and-intent` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Las tres primeras piezas del asistente: comprueba sus herramientas, recuerda lo que estaba haciendo y
clasifica el repositorio del autor en uno de los seis estados del árbol de decisión. Las reglas son
puras y se prueban con datos; la lectura del repositorio es un adaptador y se prueba contra los seis
escenarios del banco de pruebas, sin red. Los tres puntos de entrada devuelven un documento en la
salida estándar y nada más.

## Technical Context

**Language/Version**: Python 3.11 mínimo, el que declara `.python-version`.

**Primary Dependencies**: ninguna en el núcleo. `pytest` sólo para las pruebas.

**Storage**: `git config --local` para la intención pendiente. No hay archivo ni base de datos.

**Testing**: `pytest`. El dominio con datos; los adaptadores contra repositorios de verdad creados en
un directorio temporal, con un remoto local que hace de origen.

**Target Platform**: la máquina del autor, Windows incluido, y el runner de CI.

**Project Type**: núcleo del plugin de autoría más sus puntos de entrada.

**Constraints**: sólo biblioteca estándar; sólo lectura sobre el repositorio del autor; un documento
por invocación en la salida estándar.

**Scale/Scope**: tres módulos de reglas, tres adaptadores, un caso de uso y tres puntos de entrada.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | Los scripts deciden el estado, la acción y la unidad, que son hechos comprobables. El modelo decide qué decir a partir de eso. Ninguna redacción del diálogo vive en el código. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Sólo lectura: `rev-parse`, `status --porcelain`, `rev-list --count`, `remote get-url` y `config --local`. Ninguno de los que escriben, ni siquiera `fetch`. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | Los seis escenarios del banco de pruebas se ejecutan como pruebas, no como guion manual. El aviso sobre el directorio personal, que resultó ser un repositorio en esta máquina, quedó documentado en la prueba que lo descubrió. | Pasa |
| (4) Qué es dominio puro y qué adaptador | Clasificar, interpretar la intención y comprobar la versión del intérprete son datos que entran y un resultado que sale. Preguntar a git y leer los manifiestos son adaptadores. | Pasa |
| (5) Qué nombres nuevos son contrato | Los seis estados, las tres acciones y las dos claves de configuración `authoring.pendingAction` y `authoring.pendingUnit`. Los primeros ya venían del diseño; las claves se fijan aquí. | Pasa |
| (6) Qué escribe cada script y dónde | Sólo `intent.py set` y `clear`, y sólo en la configuración local del repositorio. No tocan el árbol de trabajo, y una prueba lo comprueba. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno. Las rutas de pruebas ya cubren `plugins/`. | Pasa |

## Decisiones, con su motivo

| Decisión | Motivo |
|---|---|
| Se comprueban las herramientas antes de leer la intención, y la intención antes del estado | Cada paso depende del anterior. Prometer un flujo sin tener con qué ejecutarlo es peor que no empezarlo |
| Un estado de parada sale con éxito | Detenerse es un resultado del asistente, no un fallo suyo. Sólo no poder ejecutar es un fallo. Los prototipos del diseño salían con error y se corrigió al portarlos |
| `behind_remote` y `behind_main` son campos y no un mensaje | Las reglas exigen el aviso y ningún campo lo llevaba. Un mensaje no se puede consultar; un campo sí |
| El atraso se mide con lo que hay en la copia local | Traer novedades es escribir, y aquí no se escribe. El aviso refleja la última vez que alguien las trajo, y eso ya sirve para avisar |
| Un manifiesto ilegible se dice, no se ignora | Su unidad no aparecería en la lista y el autor no entendería por qué. Callarlo convierte un archivo roto en una unidad invisible |
| Una acción guardada que no es de las válidas no se da por buena | Lo que hay en la configuración lo puede haber escrito cualquiera a mano. Se descarta y se dice por qué |
| La intención vive en la configuración local | Sobrevive a cerrar la sesión, no ensucia el árbol de trabajo y quien clona el repositorio no la hereda. Las tres cosas están probadas |
| El repositorio de pruebas se crea una vez por módulo | Crear uno por prueba costaba cuatro minutos de reloj en Windows: cada invocación de git es un proceso. Cada escenario lo devuelve al punto de partida, igual que hace el guion del banco de pruebas |

## Project Structure

### Documentation (this feature)

```text
specs/007-git-state-and-intent/
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
│   │   ├── git_state.py             los seis estados y la forma del nombre de rama
│   │   ├── intent.py                qué significa lo que quedó guardado
│   │   └── tooling.py               qué hace falta en la máquina y con qué versión
│   ├── application/author_context.py  el orden de los tres pasos
│   └── adapters/
│       ├── git.py                   mira el repositorio, sólo lee
│       ├── intent_store.py          guarda y recupera la intención
│       └── tools.py                 pregunta a la máquina qué tiene
├── skills/author-unit/scripts/
│   ├── _entry.py                    lo común a los tres: camino de búsqueda, salida y códigos
│   ├── preflight.py                 comprueba las herramientas
│   ├── git_state.py                 clasifica el repositorio
│   └── intent.py                    lee, guarda o borra la intención
└── tests/
    ├── repos.py                     los seis escenarios del banco de pruebas, sin red
    ├── test_git_state_rules.py      la clasificación, con datos
    ├── test_intent_rules.py         la interpretación, con datos
    ├── test_tooling_rules.py        la comprobación de versión, con datos
    ├── test_git_adapter.py          los seis escenarios contra repositorios de verdad
    ├── test_intent_store.py         la intención sobrevive, no ensucia y no viaja
    └── test_scripts.py              lo que el modelo consume: documento y código de salida
```

**Structure Decision**: la del plan del asistente, sin variaciones. `ports/` sigue vacío: git, la
configuración local y las herramientas de la máquina tienen implementación única, y un puerto con un
solo implementador es indirección sin beneficio.

## Complexity Tracking

Sin violaciones que justificar. Ningún módulo pasa de las 180 líneas.
