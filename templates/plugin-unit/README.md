# Unidad agrupada (plugin)

Dos archivos en la raíz de la unidad, dentro de `plugins/<<NAME>>/` del repositorio de dominio, y
después los artefactos que agrupa, cada uno copiado desde `templates/artifacts/<tipo>/`.

```
plugins/<<NAME>>/
├── .claude-plugin/plugin.json    identidad y versión DE LA UNIDAD; lo leen los dos clientes
├── GOVERNANCE.json               decisiones humanas de gobierno; lo lee la automatización y Port
├── skills/<nombre>/SKILL.md
├── agents/<nombre>.agent.md
├── commands/<nombre>.prompt.md
├── .mcp.json                     como mucho UN servidor (D2)
├── hooks/hooks.json
└── evals/<nombre>/promptfooconfig.yaml   una suite por skill, agente y prompt; obligatoria
```

## Qué rellena cada campo

| Marcador | Qué es | Ejemplo |
|---|---|---|
| `<<NAME>>` | Nombre corto de la unidad, minúsculas y guiones. Es el directorio, el `name` de `plugin.json`, la segunda mitad de `id` y lo que el usuario teclea al instalar | `cnf-migration-flow` |
| `<<REPO>>` | Repositorio de dominio que la aloja, sin organización | `agents-modernization` |
| `<<ORG>>` | Organización de GitHub | `Banca-Agente-IA-demo` |
| `<<VERSION>>` | SemVer estricto, entre comillas. Con sufijo `-beta.N` nace Experimental; sin sufijo, Producción (REGLAS-DE-VERSION.md) | `"0.1.0-beta.1"` |
| `<<DESCRIPTION>>` | Qué hace la unidad, para la vitrina del marketplace y para Port | |
| `<<TEAM>>` | Slug del equipo dueño, que debe existir en la organización | `squad-sdlc` |
| `<<CONTACT>>` | Correo del equipo, no de una persona | `squad-sdlc@bcp.com.pe` |
| `<<EXTERNAL_CONTENT>>` | Cómo trata la unidad el contenido que no controla (C3). Se borra la clave entera si el tipo no lo requiere | |

## Lo que NO va en `GOVERNANCE.json`, y dónde vive

| Dato | Dónde |
|---|---|
| Versión | `plugin.json` y la etiqueta |
| Estado (`draft`, `experimental`, ...) | Lo deriva la automatización y lo escribe en Port |
| Inventario de artefactos | El árbol |
| Quién aprobó y cuándo | La solicitud de cambio |
| Veredicto de evals y atestación | El check run y la atestación del release |
| Versión del estándar y fecha de revisión | Port, escritas por la automatización |
| Metadata de catálogo (`tags`, plataforma) | El mapa `metadata:` del frontmatter de cada artefacto (D1) |

## Campos opcionales que se añaden cuando aplican

- `risk_level`: sólo para **elevar** el riesgo calculado. Si el cálculo ya da lo que quieres, no lo pongas.
- `mcp`: **obligatorio** si la unidad lleva `.mcp.json`. Copia el bloque de `templates/artifacts/mcp/mcp-governance-block.json`.
- `deprecation`: sólo en la solicitud de cambio que anuncia la obsolescencia. Los tres campos, en una versión de parche.

`permissions` es obligatorio siempre, con las tres listas aunque estén vacías: una lista vacía afirma
que no se usa nada de ese tipo, y `rules` lo comprueba contra los agentes, los hooks y `.mcp.json`.
