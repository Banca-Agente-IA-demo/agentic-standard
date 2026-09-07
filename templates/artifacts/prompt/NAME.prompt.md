---
name: <<NAME>>
description: "<<DESCRIPTION>>"
argument-hint: "<<ARGUMENTS>>"
metadata:
  tags: <<TAGS>>
---

<!--
  DÓNDE VA: `commands/<<NAME>>.prompt.md`. El nombre del archivo sin `.prompt.md` coincide con `name`.

  EL FRONTMATTER SÓLO LLEVA LO QUE EL CLIENTE LEE más `metadata:` de catálogo. Nada de gobierno.

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
