---
name: <<NAME>>
description: "<<DESCRIPTION>>"
tools:
  - Read
  - Grep
---

# <<TITLE>>

<!--
  DÓNDE VA: `agents/<<NAME>>.agent.md`. El nombre del archivo sin `.agent.md` tiene que coincidir con
  `name`. Una sola copia: los dos clientes leen `agents/` desde la raíz de la unidad (04 §2, medido).

  EL NOMBRE ADMITE PUNTOS, que separan los niveles de la convención `{app}.{dominio}.{rol}`:
  `atla.cnf-migrator.analyst`. Medido el 24 de septiembre de 2026: el nombre con puntos carga y se
  cualifica como `plugin:atla.cnf-migrator.analyst`. Los DOS PUNTOS siguen prohibidos, porque son ese
  separador.

  EL FRONTMATTER SÓLO LLEVA LOS CUATRO CAMPOS QUE 02 §5 DECLARA: `name`, `description`, `tools` y, si
  delega, `handoffs`. NO lleva `metadata:`, que sólo existe en el formato del skill; las etiquetas de
  catálogo viven en `keywords` del plugin.json de la unidad. Nada de gobierno: el validador falla si
  reaparece id, owner, version o status.

  `tools` ES LA SUPERFICIE DE LO QUE PUEDE HACER, y la pregunta de gobierno de este tipo. Declara sólo lo
  que necesita: cada herramienta de más es alcance que hay que justificar en la revisión. Un agente que
  sólo lee no declara `Bash`. La lista es lo que se revisa y se aprueba en la solicitud de cambio.

  SI USA EL SERVIDOR MCP DE LA UNIDAD, restríngete a él en `tools` con LAS DOS GRAFÍAS a la vez, porque
  cada cliente sólo entiende la suya e ignora la otra en silencio (medido el 7 de septiembre de 2026):
      tools:
        - Read
        - "mcp__plugin_<<NAME_OF_UNIT>>_<<SERVER>>__*"
        - "<<SERVER>>/*"
  Si declaras sólo la de Claude, Copilot arranca el agente SIN el servidor y no avisa; si declaras sólo
  la de Copilot, Claude rehúsa lanzar el agente. `mcpServers:` por nombre no restringe ni valida nada en
  Claude. Un agente sin `tools` hereda TODO lo instalado en la sesión del usuario, que es lo contrario de
  C1: el validador avisa. El servidor viaja en la misma unidad que el agente que lo usa (D7).

  `model` ESTÁ PROHIBIDO (02 §5). Existe en los dos clientes y los dos lo aplican, pero no hay un valor
  que sirva a los dos: Claude Code entiende sus alias y sustituye el modelo Y SU VENTANA DE CONTEXTO;
  Copilot entiende los suyos. Un agente que fija el modelo deja de ser portable.

  SI DELEGA EN OTRO AGENTE, añade `handoffs` con `label`, `agent`, `prompt` y `send` (no `auto_send`).
  Los agentes que se invocan entre sí VIAJAN EN LA MISMA UNIDAD: en Copilot el identificador cambia a
  `plugin:agente` al empaquetar (04 §2).

  QUÉ SE EVALÚA DE UN AGENTE: el RESULTADO FINAL, no la secuencia de pasos. Fijar el orden de las
  herramientas produce pruebas que fallan cuando el agente mejora. Su suite es obligatoria y vive en
  `evals/<<NAME>>/promptfooconfig.yaml`. El caso negativo de un agente, que se invoca explícitamente y
  no puede no activarse, comprueba que SE ABSTENGA de lo que no le corresponde.

  BORRA ESTE COMENTARIO al rellenar la plantilla.
-->

## Qué hace

<<PROCEDURE>>

## Qué devuelve

<<OUTPUT>>

## Qué NO hace

<<LIMITS>>
