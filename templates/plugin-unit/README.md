# Unidad agrupada (plugin)

Un solo archivo de envoltorio en la raíz de la unidad, dentro de `plugins/<<NAME>>/` del repositorio de
dominio, y después los artefactos que agrupa, cada uno copiado desde `templates/artifacts/<tipo>/`.

```
plugins/<<NAME>>/
├── .claude-plugin/plugin.json    identidad, versión y gobierno DE LA UNIDAD
├── skills/<nombre>/SKILL.md
├── agents/<nombre>.agent.md
├── commands/<nombre>.prompt.md
├── .mcp.json                     en la raíz de la unidad; una clave por servidor
├── hooks/hooks.json
└── evals/<nombre>/promptfooconfig.yaml   una suite por skill, agente y prompt; obligatoria
```

**Un único manifiesto.** La identidad la lee el cliente para instalar; el gobierno vive dentro del
mismo archivo, en `metadata.governance`, que es el objeto que el formato de plugin reserva para datos
propios y que ningún cliente lee ni interpreta.

## Qué rellena cada marcador

| Marcador | Qué es | Ejemplo |
|---|---|---|
| `<<NAME>>` | Nombre de la unidad, minúsculas, números y guiones. Es el directorio, el `name` de `plugin.json` y lo que el consumidor teclea al instalar | `cnf-migration-flow` |
| `<<REPO>>` | Repositorio de dominio que la aloja, sin organización | `agents-modernization` |
| `<<ORG>>` | Organización de GitHub | `Banca-Agente-IA-demo` |
| `<<VERSION>>` | SemVer, entre comillas. Toda versión nace con sufijo `-beta.N` | `"0.1.0-beta.1"` |
| `<<DESCRIPTION>>` | Qué hace la unidad. Es lo que el consumidor lee en el catálogo antes de instalar | |
| `<<TEAM>>` | Equipo dueño, nunca una persona. Es a quien responde por la unidad | `squad-cnf-migration` |
| `<<TEAM_MAILBOX>>` | Buzón del equipo. Es adonde llega el aviso cuando la unidad se suspende | `squad-cnf-migration@bcp.com.pe` |
| `<<RISK_LEVEL>>` | Impacto que el autor atribuye a la unidad: `low`, `medium` o `high`. Obligatorio: informa al catálogo y no deriva aprobadores ni plazos | `medium` |

## Lo que no va en el manifiesto, y dónde vive

| Dato | Dónde |
|---|---|
| Estado del ciclo de vida | Se deriva de las marcas del release; no se escribe en ningún archivo |
| Inventario de artefactos | El árbol |
| Quién aprobó y cuándo | La solicitud de cambio |
| Veredicto de evals y atestación | El check run y la atestación del release |
| Versión del estándar y fecha de revisión | Port, escritas por la automatización |
| Etiquetas de catálogo | `keywords` de `plugin.json`, y `metadata.tags` del frontmatter de cada skill |

## Los dos bloques de gobierno que se añaden cuando aplican

- **`mcp`**: obligatorio si la unidad lleva `.mcp.json`, con una entrada por servidor. Se copia de
  `templates/artifacts/mcp/mcp-governance-block.json`.
- **`deprecation`**: sólo en la solicitud de cambio que anuncia la obsolescencia, con sus dos campos y
  en una versión de parche.
