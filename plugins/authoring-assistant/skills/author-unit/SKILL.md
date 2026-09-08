---
name: author-unit
description: Acompaña a crear, modificar o deprecar una unidad publicable del estándar agéntico. Úsalo cuando alguien quiera publicar un skill, un agente, un prompt, unos hooks o una configuración MCP, o cambiar o retirar uno que ya existe.
compatibility: Necesita Python 3.11 o superior, git, y gh con una sesión activa
---

# Autoría de una unidad publicable

<!--
  ESQUELETO DEL HITO A0. El diálogo llega en A2 y los scripts que lo sostienen en A1. Lo que hay aquí
  es sólo el marco, para que el plugin se pueda instalar y listar en los dos clientes antes de tener
  contenido.

  CUANDO SE RELLENE, la guía del diálogo se escribe y se revisa A MANO contra el árbol de decisión:
  `/speckit.implement` produce código y pruebas, no prosa de conversación.

  LO QUE ESTE ARCHIVO LLEVARÁ, por orden: el contexto mínimo, la pregunta de entrada, la de acción, la
  lectura del estado de git, cómo se retoma un trabajo a medias, y el formato único de menú. Lo largo
  vive en `references/` y se carga sólo cuando hace falta: `crear.md`, `modificar.md`, `deprecar.md`.

  BORRA ESTE COMENTARIO al rellenar el skill.
-->

## Qué es esto

Una unidad publicable es lo que se instala y se revoca de una vez: un plugin con sus artefactos, o un
artefacto solo. Toda unidad lleva su identidad y su gobierno, y pasa por las mismas reglas.

## Cómo funciona

Los scripts deciden y este skill pregunta, presenta y lee un campo de su respuesta. Nunca se
interpreta la salida de git ni el contenido de un archivo para decidir por cuenta propia: un diálogo
que interpreta a ojo se equivoca distinto cada vez y no se puede probar.

El trabajo del autor no se toca. El asistente no guarda cambios sin confirmar, no descarta nada y no
cambia de rama sobre trabajo ajeno. Si el repositorio no está en un estado que sepa manejar, se
detiene y dice qué corregir.

## Estado

Esqueleto. Todavía no hace nada: el núcleo determinístico es el hito A1 y el diálogo el A2.
