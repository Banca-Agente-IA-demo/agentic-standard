# Unidad individual (un solo artefacto)

Un artefacto que **debe poder revocarse solo** sin arrastrar a nadie, y que no obligaría a instalar
vecinos que nadie pidió (02 §2). Lleva exactamente los mismos dos archivos de envoltorio que un plugin:
identidad y versión en `plugin.json`, gobierno propio en `GOVERNANCE.json`. **No hereda nada del
repositorio ni de una unidad «de sueltos»**: ese agrupador de la demo desaparece.

```
skills/<<NAME>>/
├── .claude-plugin/plugin.json
├── GOVERNANCE.json
├── SKILL.md                           copiado de templates/artifacts/skill/
└── evals/promptfooconfig.yaml         copiado de templates/artifacts/evals/
```

Para un agente o un prompt individual, la misma forma bajo `agents/<<NAME>>/` o `commands/<<NAME>>/`,
con `agents/<<NAME>>.agent.md` o `commands/<<NAME>>.prompt.md` dentro. Para una configuración MCP sola
o unos hooks solos, `mcps/<<NAME>>/` o `hooks/<<NAME>>/` con `.mcp.json` o `hooks/hooks.json`: **medido
el 7 de septiembre de 2026 que ambos clientes los cargan** (MEDICION-HOOKS-MCP-PORTABILIDAD.md §2 y §3).

**A MEDIR antes de fijarlo en `std-002`:** si los clientes exigen que el `SKILL.md` de una unidad
individual esté bajo `skills/<<NAME>>/SKILL.md` **dentro** de la unidad (es decir,
`skills/<<NAME>>/skills/<<NAME>>/SKILL.md`) o lo aceptan en la raíz como muestra el árbol de 04 §4. La
plantilla sigue 04 §4; si la medición dice otra cosa, se ajusta la plantilla y 04, no el esquema.

Los marcadores y los campos opcionales son los mismos que en `templates/plugin-unit/README.md`.
