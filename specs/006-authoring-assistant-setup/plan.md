# Implementation Plan: El asistente de autoría existe como unidad publicable

**Branch**: `feat/006-authoring-assistant-setup` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

El plugin `authoring-assistant` con su envoltorio, el núcleo `authoring_core` en cuatro capas vacías
pero declaradas, el anclaje del validador y dos suites de pruebas: la del propio plugin, que viaja con
la unidad, y la del repositorio, que comprueba que el estándar se gobierna a sí mismo.

## Technical Context

**Language/Version**: Python 3.11 mínimo, el que declara `.python-version`.

**Primary Dependencies**: **ninguna** en el núcleo, y ése es el requisito, no una casualidad. `pytest`
sólo para las pruebas.

**Storage**: ninguno. El anclaje del validador es un archivo versionado que se lee, no un estado.

**Testing**: `pytest`. Las del plugin importan el núcleo como lo harán sus scripts; las del
repositorio pasan el validador sobre las unidades propias.

**Target Platform**: la máquina del autor, con Windows incluido, y el runner de CI.

**Project Type**: unidad publicable del estándar, con su núcleo en Python.

**Constraints**: el núcleo sólo con la biblioteca estándar; nada de carpetas vacías con archivos de
relleno; el plugin pasa sus propias reglas sin exenciones.

**Scale/Scope**: doce archivos, ninguno con lógica todavía.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | Nada todavía. El principio se hace cumplir cuando lleguen los scripts; aquí sólo se prepara la forma que lo permite. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. El esqueleto no ejecuta nada. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | Lo que se mide aquí es la instalación en los dos clientes, y es el paso que puede obligar a cambiar la forma. Se hace con el esqueleto a propósito, cuando cambiarla es barato. | Pasa |
| (4) Qué es dominio puro y qué adaptador | Las cuatro capas existen y cada una declara de qué se hace cargo. Una prueba comprueba que la capa de reglas no habla con el exterior ni importa a las demás, desde el primer commit y no cuando ya haya código. | Pasa |
| (5) Qué nombres nuevos son contrato | El nombre del plugin, el del skill, el del núcleo y las claves del anclaje del validador. Este último es nuevo y se fija aquí: repositorio, subdirectorio, etiqueta y commit. | Pasa |
| (6) Qué escribe cada script y dónde | Nada. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno. Se amplían las rutas del workflow de pruebas para cubrir `plugins/`. | Pasa |

## Decisiones, con su motivo

| Decisión | Motivo |
|---|---|
| El núcleo se llama `authoring_core`, no como el plugin | Son dos cosas distintas y el nombre debe decirlo. Y como se importa por el camino de búsqueda del lenguaje, dos plugins con un paquete del mismo nombre se pisarían en la misma sesión |
| El anclaje guarda etiqueta **y** commit | Una etiqueta de versión concreta es inmutable, pero la referencia mayor movible no lo es. El autor tiene que poder saber qué código tiene instalado sin depender de que nadie haya movido nada |
| Los permisos declaran los ejecutables desde ya | Ninguna regla automática puede contrastarlos en un skill. Si no lo declara quien lo escribe, no lo declara nadie |
| El riesgo se eleva a mano | El cálculo automático no ve que el asistente ejecuta código propio, porque lo hace sin hooks ni servidor. Elevarlo es para lo que existe el campo, y añade el aprobador que corresponde a una herramienta que escribirá en los repositorios de todos los dominios |
| No se crean las carpetas que aún no tienen contenido | Una carpeta con un archivo de relleno es un recurso huérfano, y el propio validador lo avisaría. Cada carpeta llega con la spec que la llena |
| Las pruebas del plugin corren también en el CI del repositorio | Viajan con la unidad porque el estándar lo exige, pero si sólo corrieran allí nadie las ejecutaría nunca |

## Project Structure

### Documentation (this feature)

```text
specs/006-authoring-assistant-setup/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code

```text
plugins/authoring-assistant/
├── .claude-plugin/plugin.json       identidad, versión y facetas de catálogo
├── GOVERNANCE.json                  gobierno propio: dueño, permisos, riesgo elevado
├── validator.lock                   contra qué versión del validador trabaja el autor
├── README.md                        qué es, cómo está hecho y qué necesita la máquina del autor
├── skills/author-unit/SKILL.md      el marco del diálogo, con el frontmatter portable
├── authoring_core/                  el núcleo, sólo biblioteca estándar
│   ├── domain/                      reglas puras
│   ├── application/                 casos de uso
│   ├── ports/                       el único puerto: el proveedor de releases
│   └── adapters/                    git, gh, sistema de archivos, plantillas, validador
└── tests/                           viajan con la unidad y corren en el CI del repositorio

tests/test_self_governance.py        el estándar pasa sus propias reglas sobre sus propias unidades
```

**Structure Decision**: la del diseño, sin variaciones. Los puntos de entrada vivirán en
`skills/author-unit/scripts/` y el núcleo en la raíz del plugin: no es duplicación, son el composition
root y la lógica por capas. `ports/` tendrá un único puerto, el proveedor de releases, y hay que
vigilar que siga siendo uno: git, el sistema de archivos y las plantillas tienen implementación única
y no llevan puerto.

## Complexity Tracking

Sin violaciones que justificar.
