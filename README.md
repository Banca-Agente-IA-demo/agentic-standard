# agentic-standard

Estándar agéntico de la organización: el contrato que cumplen las unidades publicables (skills,
prompts, agentes, configuraciones MCP, hooks) y los controles que lo hacen exigible.

## Qué contiene

| Carpeta | Qué es |
|---|---|
| `schemas/` | El contrato de cada tipo de artefacto y de `GOVERNANCE.json` |
| `port/` | La estructura de la ficha del catálogo de metadata |
| `.github/actions/` | Los controles reutilizables: `rules`, `evals`, `collision`, `seal`, `smoke-test` |
| `.github/workflows/` | Los workflows reutilizables (`register`, `verify`, `tag`, `publish`) y los relojes |
| `validator/` | Los controles de publicación, con sus pruebas |
| `index/` | Generación del índice de los marketplaces |
| `evals/` | Conexión del motor de evaluación con el asistente |
| `templates/` | El punto de partida de una unidad y de cada artefacto |
| `docs/` | La norma (`guidelines/`), el diseño (`design/`), las guías (`guides/`) y el material de gobierno |
| `plugins/` | Los asistentes de autoría y de consumo, que pasan por las mismas reglas que publican |
| `config/teams.json` | Mapa de cada papel del ciclo de vida al equipo de GitHub que lo ejerce |

El estándar no es sólo documentación: la norma y el código que la hace exigible se mueven en el mismo
commit.

## Cómo se trabaja aquí

Las reglas de desarrollo están en `AGENTS.md`, que leen Claude Code y GitHub Copilot CLI. Toda
capacidad empieza por una spec (Spec Kit): una spec por capacidad, una rama y un PR por spec.

## Estado

Esqueleto del hito 0. Las carpetas están vacías hasta que su spec las llene.
