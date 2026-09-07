<!--
Sync Impact Report
- Version change: plantilla sin versión -> 1.0.0 (ratificación inicial)
- Modified principles: ninguno (primera redacción)
- Added sections: Principios I a VII; Restricciones del repositorio; Flujo de trabajo y puertas de
  calidad; Gobierno
- Removed sections: ninguna
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ la sección Constitution Check es genérica y se rellena por
    plan con las puertas de la sección «Flujo de trabajo»; no hace falta cambiar la plantilla
  - .specify/templates/spec-template.md: ✅ sin secciones obligatorias nuevas
  - .specify/templates/tasks-template.md: ✅ sin categorías nuevas
  - .claude/skills/speckit-*/SKILL.md: ✅ sin referencias a esta constitución
- Follow-up TODOs: ninguno
-->

# Constitución de agentic-standard

Este repositorio es el estándar agéntico de la organización: el contrato que cumplen las unidades
publicables y los controles, workflows y asistentes que lo hacen exigible. La constitución fija los
principios que ninguna spec puede contradecir. La fuente de cada spec son los lineamientos 02, 03 y 04
y los documentos de diseño del asistente; la constitución no repite su contenido.

## Principios

### I. Los scripts deciden; el modelo pregunta, presenta y lee un campo del JSON

Toda decisión que dependa del estado del repositorio, de una versión, de un riesgo o de un diff la toma
un script determinístico y la expresa en un JSON en `stdout`. El modelo formula preguntas cerradas al
usuario, presenta el resultado y actúa sobre un campo concreto de ese JSON. El modelo NUNCA interpreta
la salida de git, un diff ni un archivo de gobierno para decidir por su cuenta.

Razón: un diálogo que interpreta git a ojo se equivoca de forma distinta cada vez y no se puede probar.
Un script se prueba una vez y se equivoca siempre igual, que es corregible.

### II. Nunca se toca trabajo ajeno; todo el estado vive en git; relee, no recuerdes

Los scripts que corren en el repositorio de un autor sólo ejecutan `fetch`, `switch -c`, `add`,
`commit` y `push` de la rama `<accion>/<unidad>` actual, y `gh pr create` sobre ella. NUNCA `stash`,
`reset`, `checkout` de archivos ajenos ni operación alguna sobre otra rama. Un estado de git distinto
de los aceptados detiene al asistente con el mensaje de qué corregir. El estado que hay que retomar se
guarda en git (configuración local del repositorio), no en la memoria de la conversación: cada paso lo
relee antes de actuar.

Razón: el repositorio del autor no es del asistente. Un `stash` o un `reset` que borra trabajo sin
commit es irreversible y destruye la confianza en la herramienta.

### III. Los dos clientes son obligatorios y Copilot CLI es el de referencia

Todo lo que el asistente o los plugins hagan DEBE funcionar en GitHub Copilot CLI y en Claude Code. Lo
que sólo uno ofrece es mejora, no requisito, y no puede ser el único camino. Una capacidad que sólo
funciona en un cliente NO se da por cerrada. Se mide en los dos antes de declararla hecha.

Razón: BCP tiene estandarizado Copilot CLI; el equipo construye con Claude Code. Cerrar una capacidad
probada sólo en el segundo la entrega rota al usuario real.

### IV. Dominio puro y probado sin disco ni red; adaptadores con dobles inyectados; toda medición es prueba

El código se organiza por capas (`domain/`, `application/`, `ports/`, `adapters/`, entry points). El
dominio NO importa `subprocess`, `pathlib` ni nada del proyecto fuera de `domain/`: versión, riesgo,
aprobadores y clasificación del diff se prueban con datos, sin repositorio. Los adaptadores se
sustituyen por inyección en la firma, nunca con parches de módulo. Todo comportamiento medido en un
cliente o en GitHub se convierte en prueba de regresión con un comentario que dice dónde se midió.

Razón: la testabilidad es la justificación de la arquitectura. Lo que no se puede probar sin levantar
el mundo no está bien separado.

### V. Identificadores en inglés, prosa en español; los nombres del árbol y las reglas son contrato

Módulos, funciones, variables, claves JSON, ids de job y nombres de paso van en inglés. Comentarios,
docstrings, mensajes al usuario y documentación van en español. Los nombres que otros sistemas
emparejan por texto NO se renombran: los tres requeridos del ruleset (`verify / rules`,
`verify / evals-verdict`, `verify / collision`), los workflows reutilizables (`register`, `verify`,
`tag`, `publish`, `rebuild-index`) y los jobs de sus llamadores, el evento `version-published`, las
claves de `GOVERNANCE.json` y del blueprint de Port, y los estados y campos del árbol de decisión y de
las reglas de rama y versión. Renombrar uno de ellos es una migración, no un refactor.

Razón: el contrato de datos ya está en inglés y un ruleset empareja por texto exacto; renombrar un
requerido dejó bloqueados todos los PR dos veces en la demo anterior.

### VI. Todo script que escribe valida el destino y no lee credenciales

Antes de escribir, un script comprueba que la ruta de destino está bajo la raíz de la unidad elegida y
se detiene si no lo está. Ningún script lee variables de entorno de credenciales ni archivos de
secretos. El que necesita arrancar un servidor MCP para consultar sus herramientas lo hace sólo tras
confirmación explícita del autor.

Razón: un script que escribe fuera de la unidad o que lee una credencial por error es un incidente de
seguridad, no un bug.

### VII. Un workflow por evento, un job por responsabilidad

Cada workflow responde a un solo evento de GitHub. Los llamadores de los dominios no llevan lógica:
invocan al reutilizable con `uses: …@v1` y le pasan permisos mínimos por job y los secretos que
necesita. Los reutilizables usan tokens efímeros de la App del ciclo de vida, `@v1` para lo propio y
SHA para terceros, `if: failure()` para avisar y nunca `continue-on-error` sin capturar el resultado.
Ningún paso termina en verde sin haber hecho su trabajo. Ningún workflow supera 150 líneas sin
justificación escrita en su cabecera.

Razón: la demo anterior acumuló workflows de varios eventos y jobs con varias responsabilidades que
nadie podía leer ni proteger con un ruleset.

## Restricciones del repositorio

- Python 3.11 o superior. El asistente de autoría usa sólo la biblioteca estándar; el validador puede
  depender de paquetes y se instala como paquete desde git en un entorno privado.
- Las reglas de código detalladas (G, P, OO, L, PM, T) están en `AGENTS.md` y son de obligado
  cumplimiento; `CLAUDE.md` sólo lo importa. Nada de lo que hay en la raíz del repositorio se
  distribuye; los plugins de `plugins/` se distribuyen enteros.
- No se usan dependencias entre unidades publicables: se agrupa o se copia.
- Sin em-dashes en ningún documento ni comentario.

## Flujo de trabajo y puertas de calidad

- Ninguna capacidad empieza por el código. Una spec por capacidad en `specs/NNN-<nombre>/`, una rama
  `feat/NNN-<nombre>` y un PR por spec con la spec enlazada. Ninguna spec cubre más de dos scripts o un
  camino del árbol de decisión.
- Orden: `specify`, `clarify`, `checklist`, `plan`, `tasks`, `analyze`, `implement`. Lo que el árbol
  deja abierto se decide en `clarify` y se anota en la spec, nunca en el código.
- El `SKILL.md`, los `references/` y los documentos de diseño se escriben y revisan a mano;
  `implement` produce código y pruebas, no la guía del diálogo.
- Puertas del Constitution Check de cada plan: (1) qué decide un script y qué hace el modelo;
  (2) qué comandos de git ejecuta y sobre qué rama; (3) qué se mide en cada cliente y cómo se convierte
  en prueba; (4) qué es dominio puro y qué adaptador; (5) qué nombres nuevos son contrato; (6) qué
  escribe cada script y dónde; (7) qué eventos y jobs añade cada workflow.
- Las pruebas del dominio corren en CI en cada PR que toque el código. Lo que decide si algo se publica
  (validador, reglas, generador de índice) tiene pruebas propias.

## Gobierno

Esta constitución prevalece sobre cualquier otra práctica del repositorio. Una enmienda es un PR que
modifica este archivo, explica el motivo y actualiza el Sync Impact Report; la aprueba el equipo de
plataforma. La versión sigue SemVer: MAJOR si se elimina o redefine un principio, MINOR si se añade uno
o se amplía materialmente, PATCH si se aclara la redacción. Toda revisión de PR comprueba el
Constitution Check del plan de su spec; una desviación se justifica por escrito en el plan o no se
fusiona.

**Version**: 1.0.0 | **Ratified**: 2026-09-07 | **Last Amended**: 2026-09-07
