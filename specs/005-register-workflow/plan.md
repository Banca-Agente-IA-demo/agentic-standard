# Implementation Plan: El registro de un cambio en una rama de trabajo

**Branch**: `feat/005-register-workflow` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Tres piezas. Una **composite action** `validate` que instala el validador desde el propio árbol del
estándar y aplica las reglas. Un **workflow reutilizable** `register.yml` que la orquesta con permisos
mínimos. Un **llamador** en el dominio, de veinte líneas, que dice cuándo. Más el modo de
descubrimiento en el validador, para que el YAML no lleve lógica.

## Technical Context

**Language/Version**: Python 3.11 mínimo, igual que el resto. El runner usa 3.11 para parecerse al
suelo declarado, no a la versión de desarrollo.

**Primary Dependencies**: las del validador. Ninguna nueva.

**Storage**: ninguno. El registro no escribe en el repositorio.

**Testing**: `pytest` para el descubrimiento de unidades, con repositorios de git de mentira creados
en `tmp_path`. El workflow se prueba ejecutándolo de verdad sobre una rama del dominio.

**Target Platform**: runner de GitHub y la máquina del autor.

**Project Type**: automatización de integración continua más una ampliación del validador.

**Constraints**: el llamador no lleva lógica; ningún paso puede terminar en verde sin trabajar; sin
`paths:` en el disparador; acciones de terceros fijadas a SHA completo.

**Scale/Scope**: de cero a un puñado de unidades por push.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | No hay modelo. El descubrimiento y las reglas los decide el validador; el YAML sólo los invoca. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Sólo lectura: `git diff` y `git rev-parse` sobre el árbol ya clonado. No cambia de rama, no escribe, no toca el trabajo de nadie. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | No depende de ningún cliente. Lo que se mide aquí es de la plataforma: que la composite action resuelve el árbol del estándar sin token, y que la comprobación aparece con el nombre esperado. Se comprueba ejecutándola. | Pasa |
| (4) Qué es dominio puro y qué adaptador | Dominio: la función que, dados los archivos cambiados y las raíces de unidad, dice qué unidades se tocaron. Adaptador: el que pregunta a git y el que recorre el árbol. | Pasa |
| (5) Qué nombres nuevos son contrato | El nombre de la comprobación `register / rules`, el del workflow reutilizable, el de la composite action y la referencia movible con la que los dominios la invocan. | Pasa |
| (6) Qué escribe cada script y dónde | Nada en el repositorio. Informe a la salida estándar y al resumen de la ejecución. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | El reutilizable no tiene disparador propio, sólo invocación. El llamador tiene un evento, push a rama distinta de la principal, y un job. Ninguno de los dos pasa de 150 líneas. | Pasa |

## Decisiones de diseño, con su motivo

| Decisión | Motivo |
|---|---|
| El control vive en una **composite action**, no en pasos del reutilizable | Medido: la credencial por defecto de un workflow está acotada al repositorio del llamador y no puede clonar el estándar cuando es privado, que es el caso de BCP. Una composite action se resuelve por la política de acceso de la organización y llega con el árbol del estándar dentro, sin necesitar ninguna credencial |
| El validador se instala **desde ese árbol**, no de la red | La versión del validador queda atada por construcción a la del workflow. Nadie teclea una versión y no pueden separarse |
| **Sin matriz** por unidad | Un push a una rama de trabajo toca una o dos unidades y el validador recorre varias en un proceso. Una matriz vacía tumba la ejecución en lugar de saltarla, y ese modo de fallo no compensa aquí |
| El descubrimiento va **en el validador**, no en el YAML | Un guion incrustado no se puede probar, y esta es justo la clase de lógica que se rompe en silencio |
| **Sin `paths:`** en el disparador | Medido: con un filtro de rutas la comprobación no se reporta cuando no hay coincidencia, y una comprobación requerida que dependa de eso deja la solicitud esperando para siempre. Aunque el registro no sea requerido, el patrón no se introduce |
| El llamador **cancela** la ejecución anterior de la misma rama | Es el único sitio del diseño donde cancelar es correcto: sólo interesa el último estado de la rama |
| **Sin la App** del ciclo de vida | El registro sólo lee el árbol y no escribe nada. La credencial por defecto basta. La regla que necesitaría preguntar por los equipos de la organización no está en el validador, precisamente por esto |

## Project Structure

### Documentation (this feature)

```text
specs/005-register-workflow/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code

```text
agentic-standard/
├── .github/
│   ├── actions/validate/action.yml     composite: instala el validador y aplica las reglas
│   └── workflows/register.yml          reutilizable: un job, permisos mínimos
└── validator/agentic_validator/
    ├── domain/discovery.py             puro: archivos cambiados más raíces de unidad da unidades
    ├── adapters/repository.py          git y recorrido del árbol
    └── cli.py                          modo de descubrimiento del comando

agents-modernization/
└── .github/workflows/register.yml      el llamador, sin lógica

tests/validator/
├── test_discovery.py                   la regla pura, con datos
└── test_repository.py                  el adaptador, con repositorios de git en tmp_path
```

**Structure Decision**: el descubrimiento entra en el validador y no en un paquete aparte porque el
asistente de autoría del hito 2 necesita exactamente lo mismo en la máquina del autor, y duplicarlo
sería la primera grieta entre lo que ve el autor y lo que ve la automatización.

## Cómo se cierra el hito

El criterio del plan es que un push a una rama de trabajo del dominio corra la comprobación en verde
sobre una unidad hecha de las plantillas. Se toma en la rama de trabajo, que es donde el flujo ocurre.
El repositorio de dominio no puede fusionar a su rama principal hasta que exista la verificación,
porque su protección exige tres comprobaciones que todavía nadie emite; eso es del hito 3 y está
previsto.

## Complexity Tracking

Sin violaciones que justificar.
