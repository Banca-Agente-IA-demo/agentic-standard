# Unidad individual (un solo artefacto)

Un artefacto que **debe poder revocarse solo** sin arrastrar a nadie, y que no obligaría a instalar
vecinos que nadie pidió (02 §2). Lleva exactamente el mismo archivo de envoltorio que un plugin:
identidad, versión y gobierno propio en `plugin.json`. **No hereda nada del repositorio ni de una
unidad «de sueltos»**: ese agrupador de la demo desaparece.

```
skills/<<NAME>>/
├── .claude-plugin/plugin.json
├── SKILL.md                           copiado de templates/artifacts/skill/
└── evals/promptfooconfig.yaml         copiado de templates/artifacts/evals/
```

Para un agente o un prompt individual, la misma forma bajo `agents/<<NAME>>/` o `commands/<<NAME>>/`,
con `agents/<<NAME>>.agent.md` o `commands/<<NAME>>.prompt.md` dentro. Para una configuración MCP sola
o unos hooks solos, `mcps/<<NAME>>/` o `hooks/<<NAME>>/` con `.mcp.json` o `hooks/hooks.json`: **medido
el 7 de septiembre de 2026 que ambos clientes los cargan** (MEDICION-HOOKS-MCP-PORTABILIDAD.md §2 y §3).

**MEDIDO el 16 de septiembre de 2026** en Claude Code 2.1.272 y Copilot CLI 1.0.85, experimento 6 de
`experimentos/06-unidades-individuales/`. La plantilla era correcta y se confirma entera:

| Artefacto | Dónde va, medido | Qué pasa si se aplana a la raíz |
|---|---|---|
| `SKILL.md` | **La raíz de la unidad** | No aplica: es la forma correcta, y la subcarpeta también funcionaría |
| `.mcp.json` | **La raíz de la unidad** | No aplica: es su única posición, igual que en un plugin |
| `agents/<<NAME>>.agent.md` | Su subcarpeta | **Instala con mensaje de éxito y no carga nada.** `Agents (0)` en Claude, ausente de la lista de Copilot |
| `commands/<<NAME>>.prompt.md` | Su subcarpeta | Igual: instala y no carga, en los dos clientes |
| `hooks/hooks.json` | Su subcarpeta | Claude no lo registra ni dispara; Copilot sí lo tolera. **La subcarpeta es la única forma portable** |

La regla que resume las cinco filas: **cada artefacto vive donde viviría dentro de un plugin, salvo el
`SKILL.md` y el `.mcp.json`, que van en la raíz de la unidad.** Y ninguno de los tres fallos avisa: el
plugin queda instalado y habilitado, así que el control `layout` es quien tiene que pararlo, y desde
esta misma fecha lo hace con la regla `layout.artifact-flattened-at-root`.

Los marcadores y los campos opcionales son los mismos que en `templates/plugin-unit/README.md`.
