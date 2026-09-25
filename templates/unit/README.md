# El manifiesto de la unidad

**Un solo archivo para las dos formas.** El documento 01 §1 dice que la unidad agrupada y la
individual llevan exactamente los mismos manifiestos, y esta plantilla es esa afirmación hecha
archivo: lo único que cambia entre ambas es **dónde la copia el sembrador**, y esa ruta no vive
dentro del archivo.

| Forma | Dónde se copia |
|---|---|
| Agrupada | `plugins/<<NAME>>/.claude-plugin/plugin.json` |
| Individual | `<tipo>/<<NAME>>/.claude-plugin/plugin.json` |

## Qué rellena cada marcador

| Marcador | Qué es | Ejemplo |
|---|---|---|
| `<<NAME>>` | Nombre de la unidad, minúsculas, números y guiones. Es el directorio, el `name` del manifiesto y lo que el consumidor teclea al instalar | `cnf-migration-flow` |
| `<<VERSION>>` | SemVer, entre comillas. Toda versión nace con sufijo de prelanzamiento | `"0.1.0-beta.1"` |
| `<<DESCRIPTION>>` | Qué hace la unidad. Es lo que el consumidor lee en el catálogo antes de instalar | |
| `<<TEAM>>` | Equipo dueño, nunca una persona | `squad-cnf-migration` |
| `<<TEAM_MAILBOX>>` | Buzón del equipo. Es adonde llega el aviso cuando la unidad se suspende | `squad-cnf-migration@bcp.com.pe` |
| `<<ORG>>` | Organización de GitHub | `Banca-Agente-IA-demo` |
| `<<REPO>>` | Repositorio de dominio que la aloja, sin organización | `agents-modernization` |
| `<<RISK_LEVEL>>` | `low`, `medium` o `high`. Informa al catálogo; no deriva aprobadores ni plazos | `medium` |

## Los dos bloques de gobierno que no están en la plantilla

Ninguno de los dos es estático, así que los añade el sembrador o el asistente, no un marcador:

- **`mcp`**, una entrada por servidor declarado, con su `accountable_team`. Su forma está en
  `templates/artifacts/mcp/mcp-governance-block.json`.
- **`deprecation`**, sólo en la solicitud de cambio que anuncia la obsolescencia.
