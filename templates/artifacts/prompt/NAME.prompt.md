---
name: <<NAME>>
description: "<<DESCRIPTION>>"
argument-hint: "<<ARGUMENTS>>"
---

<!--
  DÓNDE VA: `commands/<<NAME>>.prompt.md`. El nombre del archivo sin `.prompt.md` coincide con `name`.

  EL NOMBRE ADMITE PUNTOS, con el mismo criterio que el agente: `atla.cnf-migration.analyze`.

  EL FRONTMATTER SÓLO LLEVA LOS CAMPOS QUE 02 §6 DECLARA: `name`, `description`, y si aplica
  `argument-hint` y `agent`. NO lleva `metadata:`; las etiquetas de catálogo viven en `keywords` del
  plugin.json de la unidad. Nada de gobierno. `model` está prohibido.

  UN PROMPT ES UN PUNTO DE ENTRADA que una persona invoca a mano, a diferencia de un skill, que el
  modelo decide cargar. Regla de desistimiento: ante la duda entre prompt y skill, elige skill. La
  diferencia se está borrando aguas arriba, así que no construyas nada que dependa de que sigan siendo
  cosas distintas.

  CONSECUENCIA PARA SU EVALUACIÓN: un prompt no tiene eje de activación que medir; queda la calidad de la
  salida. Su suite es obligatoria igual y vive en `evals/<<NAME>>/promptfooconfig.yaml`.

  SI DELEGA EN UN AGENTE, decláralo con `agent: <<AGENT_NAME>>`, un agente de LA MISMA UNIDAD.

  `argument-hint` es la pista que el cliente muestra al teclear el comando. Si no acepta argumentos,
  borra la clave en vez de dejarla vacía.

  BORRA ESTE COMENTARIO al rellenar la plantilla.
-->

# <<TITLE>>

<<INSTRUCTIONS>>
