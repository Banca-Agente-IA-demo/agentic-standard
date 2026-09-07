# Data Model: Prueba de humo de la organización

Entidades del dominio. Todas son `@dataclass(frozen=True)` o `Enum`; ninguna hace I/O. Los nombres
son identificadores en inglés (constitución V).

## Contract (constantes, `domain/contract.py`)

Nombres que el estándar fija y que nadie renombra sin migración.

| Constante | Valor | Origen |
|---|---|---|
| `APP_SLUG` | `agentic-lifecycle` | guía §4 |
| `APP_SECRET_NAMES` | `APP_ID`, `APP_PRIVATE_KEY` | guía §7 |
| `MARKETPLACE_VARIABLE_NAMES` | `INDEX_CHANNEL`, `AGENTIC_TOPIC` | guía §7 |
| `DOMAIN_TOPIC` | `agentic-unit` | guía §2 |
| `MAIN_RULESET_NAME` | `protect-main` | clarify 5 |
| `TAGS_RULESET_NAME` | `protect-tags` | clarify 5 |
| `REQUIRED_CONTEXTS` | `verify / rules`, `verify / evals-verdict`, `verify / collision` | guía §9 |
| `ACTIONS_INTEGRATION_ID` | `15368` | guía §9 |

## Environment (`domain/environment.py`)

Valores esperados de una organización concreta. Se carga de `environments/<name>.json`.

| Campo | Tipo | Ejemplo demo | Notas |
|---|---|---|---|
| `name` | `str` | `demo` | nombre del archivo |
| `organization` | `str` | `Banca-Agente-IA-demo` | |
| `plan` | `str` | `free` | `enterprise` en BCP |
| `default_repository_permission` | `str` | `read` | `none` en BCP |
| `members_can_create_repositories` | `bool` | `false` | |
| `platform_repositories` | `tuple[str, ...]` | `agentic-standard` | reciben los secretos de la App |
| `marketplaces` | `tuple[Marketplace, ...]` | ver abajo | reciben secretos y variables |
| `domain_repositories` | `tuple[str, ...]` | `agents-modernization` | reciben secretos, topic y rulesets |

**Marketplace**: `repository: str`, `channel: IndexChannel` (`production` | `experimental`).

Reglas de validación al cargar: `organization` no vacío; al menos un marketplace; los canales de los
marketplaces son distintos entre sí; ningún repositorio aparece en dos listas.

**Team roster** (de `config/teams.json`): conjunto de slugs esperados. Se deriva recorriendo
`platform_team`, `control_functions.*`, `pilot_team` y, por cada dominio, `technical_lead` y
`champion`. El nombre `TeamRoster` es una entidad de dominio; su carga es un adaptador.

## OrganizationSnapshot (`ports/github_reader.py`)

Lo observado en GitHub, ya parseado, sin decidir nada. Cada campo es `Observed[T]`: o un valor `T`,
o una `Unavailable(reason: str)` cuando la consulta falló. Así el dominio distingue «falta» de «no
se pudo mirar» sin excepciones.

| Campo | Tipo observado |
|---|---|
| `organization` | `OrganizationSettings(plan, default_repository_permission, members_can_create_repositories)` |
| `team_slugs` | `frozenset[str]` |
| `app_installation` | `AppInstallation(app_slug, repository_selection, repositories: frozenset[str] \| None) \| None` |
| `secret_names_by_repository` | `dict[str, frozenset[str]]` |
| `variables_by_repository` | `dict[str, dict[str, str]]` |
| `repositories_with_topic` | `frozenset[str]` |
| `rulesets_by_repository` | `dict[str, tuple[Ruleset, ...]]` |

**Ruleset**: `name`, `enforcement` (`active` | `evaluate` | `disabled`), `target` (`branch` | `tag`),
`required_contexts: tuple[RequiredContext, ...]`. **RequiredContext**: `context`, `integration_id`.

El puerto `GitHubReader` es un `Protocol` con métodos que devuelven cada pieza observada; el caso de
uso los compone en el snapshot. Dos implementaciones: `GhCliReader` y el doble de las pruebas.

## CheckResult y Report (`domain/report.py`)

| Entidad | Campos |
|---|---|
| `CheckStatus` (Enum) | `PASSED`, `FAILED`, `UNCHECKED` |
| `CheckResult` | `check_id: str`, `scope: str` (organización, repo o equipo), `status`, `expected: str \| None`, `found: str \| None`, `detail: str` |
| `Report` | `environment_name`, `results: tuple[CheckResult, ...]` |
| `Verdict` (Enum) | `PASS` (código 0), `FAIL` (1), `UNCHECKED` (2) |

Regla del veredicto: `UNCHECKED` si alguna comprobación es `UNCHECKED`; si no, `FAIL` si alguna es
`FAILED`; si no, `PASS`. Es una función pura de `Report`.

## Checks (`domain/checks.py`)

Cada comprobación es una función pura `(snapshot, environment, roster) -> tuple[CheckResult, ...]`.
Una lista ordenada las agrupa y el caso de uso la recorre entera (FR-009).

| `check_id` | FR | Ámbito | Qué compara |
|---|---|---|---|
| `org.settings` | FR-001 | organización | plan, permiso base, creación de repos |
| `teams.exist` | FR-002 | equipo | cada slug del roster está en `team_slugs` |
| `app.installed` | FR-003 | organización | hay instalación con `APP_SLUG`; `all` o `selected` que cubre todos los repos esperados |
| `secrets.present` | FR-004 | repositorio | cada repo esperado tiene los dos nombres exactos |
| `variables.present` | FR-005 | repositorio | cada marketplace tiene las dos variables y `INDEX_CHANNEL` igual a su canal |
| `topic.domains` | FR-006 | repositorio | todos los dominios lo llevan; ningún otro repo lo lleva |
| `rulesets.present` | FR-007 | repositorio | cada dominio tiene `protect-main` y `protect-tags` activos |
| `rulesets.contexts` | FR-008 | repositorio | `protect-main` exige exactamente `REQUIRED_CONTEXTS` con `ACTIONS_INTEGRATION_ID` |

Cuando el campo observado que necesita una comprobación es `Unavailable`, la comprobación devuelve
`UNCHECKED` con la razón, y no intenta deducir nada.
