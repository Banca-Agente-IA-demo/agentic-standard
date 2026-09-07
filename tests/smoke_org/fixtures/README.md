# Fixtures de `gh` para la prueba de humo

Respuestas reales capturadas el **2026-09-07** contra la organización `Banca-Agente-IA-demo` con
`gh` 2.92, cuenta `SAUL-VIDAL-NTT` (ámbitos `admin:org`, `repo`, `workflow`). Cada prueba que las usa
es una prueba de regresión de la forma de respuesta (T3): si GitHub o `gh` cambian el formato, la
fixture se vuelve a capturar con el mismo comando y se anota aquí la fecha.

| Archivo | Comando | Qué se usa |
|---|---|---|
| `org.json` | `gh api orgs/Banca-Agente-IA-demo` | `plan.name`, `default_repository_permission`, `members_can_create_repositories` |
| `teams.json` | `gh api orgs/Banca-Agente-IA-demo/teams --paginate` | `[].slug` |
| `installations.json` | `gh api orgs/Banca-Agente-IA-demo/installations` | `installations[].app_slug`, `.repository_selection`, `.id` |
| `secret_list.json` | `gh secret list --repo Banca-Agente-IA-demo/agentic-standard --json name` | `[].name` |
| `variable_list.json` | `gh variable list --repo Banca-Agente-IA-demo/agentic-marketplace --json name,value` | `[].name`, `[].value` |
| `repo_list_topic.json` | `gh repo list Banca-Agente-IA-demo --topic agentic-unit --json name --limit 1000` | `[].name` |
| `rulesets_list.json` | `gh api repos/Banca-Agente-IA-demo/agents-modernization/rulesets` | `[].id`, `.name`, `.enforcement`, `.target`; no trae reglas |
| `ruleset_protect_main.json` | `gh api repos/Banca-Agente-IA-demo/agents-modernization/rulesets/22463950` | `rules[type=required_status_checks].parameters.required_status_checks[]` |
| `ruleset_protect_tags.json` | `gh api repos/Banca-Agente-IA-demo/agents-modernization/rulesets/22463954` | `enforcement`, `target` |
| `gh_unauthorized.json` | `GH_TOKEN=invalid gh api orgs/Banca-Agente-IA-demo/installations` | Cuerpo en `stdout` con `message`; `stderr` `gh: Bad credentials (HTTP 401)`; código de salida 1 |

Observación medida: cuando `gh api` falla, el cuerpo JSON del error va a `stdout` y el resumen
`gh: <mensaje> (HTTP <código>)` va a `stderr`, con código de salida 1. El lector usa el `message` del
cuerpo si puede parsearlo y, si no, la última línea de `stderr`.
