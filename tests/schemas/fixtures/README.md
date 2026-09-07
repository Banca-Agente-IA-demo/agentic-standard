# Instancias de ejemplo de los esquemas

Copiadas el **7 de septiembre de 2026** de `track-agentico/docs/diseno-flujos/hito-1-esquemas-y-plantillas/examples/`,
el paquete de diseño del hito 1, cuya autocomprobación (`selfcheck.py`) estaba en verde.

| Archivo | Qué representa |
|---|---|
| `governance-plugin-with-mcp.json` | Unidad agrupada completa: riesgo elevado, permisos, contenido externo y el bloque de gobierno de su único servidor MCP con credenciales y custodio |
| `governance-individual-deprecated.json` | Unidad individual mínima, obsoleta y **sin sucesor** (`superseded_by: none`, decisión D6) |
| `marketplace-exp.claude-code.json` | Índice del canal experimental en la proyección de Claude Code: fuente `git-subdir` |
| `marketplace-exp.copilot.json` | El mismo índice en la proyección de Copilot CLI: fuente `github` con `path` |

Los dos índices listan la misma unidad y la misma versión con sufijo de prelanzamiento. Se diferencian
sólo en cómo direccionan un subdirectorio, que es la divergencia medida entre clientes.

**Los esquemas no se editan aquí.** Una corrección se hace primero en el paquete de diseño, se
comprueba con su `selfcheck.py` y después se copia a `schemas/`. Estas fixtures se actualizan en el
mismo movimiento.
