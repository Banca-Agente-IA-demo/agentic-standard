# Research: Prueba de humo de la organización

Fase 0 del plan. Cada decisión lleva su razón y las alternativas descartadas. Las formas de
respuesta se midieron contra `Banca-Agente-IA-demo` el 2026-09-07 con `gh` 2.92.

## R1. Cómo se consulta GitHub

**Decision**: a través de `gh api` en un subproceso, construido con listas (P10), usando la sesión
que la persona ya tiene autenticada. El adaptador pide JSON y lo parsea; el dominio nunca ve `gh`.

**Rationale**: la constitución VI prohíbe que los scripts lean credenciales. `gh` ya resuelve
autenticación, SSO de la Enterprise en BCP y paginación. La guía §10 está escrita en comandos `gh`, de
modo que cada comprobación tiene su comando de referencia. Y `gh` es requisito declarado del
asistente de autoría, así que no añade dependencias.

**Alternatives considered**:
- `urllib` con un token de una variable de entorno: obliga a leer una credencial; descartado por VI.
- Un token de la App del ciclo de vida: la App no tiene permisos para leer secretos ni ajustes de
  organización, y añadirlos contradice la guía §4; descartado.
- PyGithub o `requests`: dependencias en tiempo de ejecución que la constitución no quiere para las
  herramientas de la plataforma; descartado.

## R2. Dónde viven los valores esperados

**Decision**: un JSON por entorno en `tools/smoke_org/environments/` (`demo.json`, `bcp.json`), con
nombre de la organización, plan, permiso base, creación de repositorios, repositorios de plataforma,
marketplaces con su canal y repositorios de dominio. Los nombres de equipo salen de
`config/teams.json` del propio repositorio, no del JSON de entorno (FR-002).

**Rationale**: FR-013 exige separar valores esperados de comprobaciones. Un archivo por entorno hace
que cambiar de demo a BCP sea elegir otro archivo (SC-005). `bcp.json` se entrega como plantilla con
los valores que BCP debe fijar, para que la migración no empiece de cero.

**Alternatives considered**:
- Flags de línea de comandos para cada valor: una docena de flags, imposible de reproducir; descartado.
- Un solo archivo con dos secciones: mezcla entornos y tienta a compartir valores; descartado.

## R3. Dónde viven los nombres contrato

**Decision**: un módulo de dominio `contract.py` con constantes: nombres de los dos secretos, de las
dos variables, del topic, de la App, de los dos rulesets, los tres contextos requeridos y el
`integration_id` de GitHub Actions (15368).

**Rationale**: FR-014 pide una sola definición. Hoy los workflows reutilizables no existen; cuando
lleguen, este módulo es la referencia que deben respetar. Los archivos `github/rulesets/*.json` del
espacio de trabajo están fuera de este repositorio: la prueba los verifica indirectamente comprobando
lo que hay en GitHub, que es lo que importa.

**Alternatives considered**:
- Leer los contextos de `github/rulesets/protect-main.json`: está fuera del repo y la prueba debe
  funcionar clonando sólo el estándar; descartado.

## R4. Estructura del paquete y forma de ejecución

**Decision**: paquete `smoke_org` bajo `tools/`, declarado en `pyproject.toml` con
`[tool.setuptools.packages.find] where = ["tools"]` y un script de consola `smoke-org`. Instalación
en modo editable: `pip install -e ".[dev]"`. Ejecución: `smoke-org --env demo`. Pruebas: `pytest`.

**Rationale**: evita `PYTHONPATH` y `sys.path` en un repositorio que se instala igual en la máquina
y en CI. El asistente de autoría sí ajusta `sys.path` porque se distribuye sin instalar; esta
herramienta no se distribuye, así que la instalación editable es la vía normal.

**Alternatives considered**:
- `python tools/smoke_org.py` con `sys.path` a mano: funciona, pero los tests necesitan la misma
  maniobra y se duplica; descartado.
- `uv` como gestor: el plan del asistente lo menciona; para una dependencia de desarrollo no aporta
  y añade una herramienta a la imagen de CI. Se puede adoptar después sin cambiar el `pyproject`.

## R5. Códigos de salida y salida

**Decision**: `0` pasa, `1` no pasa, `2` no se pudo comprobar (prevalece sobre `1`). Informe de texto
en `stdout`; logging en `stderr` con `--verbose` para `DEBUG` (L5, L8). Sin `--json` en esta spec.

**Rationale**: FR-012 pide tres indicadores; los códigos de salida son lo que otro proceso consume
sin leer el informe. El informe en texto es lo que la persona lee. Un formato JSON de salida no tiene
consumidor hoy; se añade cuando lo tenga (no sobre-ingeniería).

**Alternatives considered**:
- Un solo código distinto de cero: no distingue «rojo» de «no sé», que es la aclaración 3; descartado.

## R6. Formas de respuesta de `gh` medidas

Medidas el 2026-09-07 contra la organización de demo; cada una será una fixture de prueba.

| Comprobación | Comando | Campos usados |
|---|---|---|
| Organización | `gh api orgs/<org>` | `plan.name`, `default_repository_permission`, `members_can_create_repositories` |
| Equipos | `gh api orgs/<org>/teams --paginate` | `[].slug` |
| App | `gh api orgs/<org>/installations` | `installations[].app_slug`, `.repository_selection` (`all` o `selected`), `.id` |
| Repos de una instalación selectiva | `gh api user/installations/<id>/repositories` | `repositories[].name` (sólo si `selected`) |
| Secretos | `gh secret list --repo <org>/<repo> --json name` | `[].name` |
| Variables | `gh variable list --repo <org>/<repo> --json name,value` | `[].name`, `[].value` |
| Topic | `gh repo list <org> --topic <topic> --json name --limit 1000` | `[].name` |
| Rulesets | `gh api repos/<org>/<repo>/rulesets` | `[].id`, `.name`, `.enforcement`, `.target` |
| Contextos | `gh api repos/<org>/<repo>/rulesets/<id>` | `rules[type=required_status_checks].parameters.required_status_checks[].{context,integration_id}` |

Observaciones que condicionan el diseño:
- `gh secret list` sin `--json` imprime tabla; con `--json name` devuelve lista. Se usa siempre `--json`.
- La instalación de la App puede ser `all`; entonces no hace falta la segunda llamada.
- `gh api repos/.../rulesets` (lista) no incluye las reglas; hay que pedir cada ruleset por `id`.
- Un `gh` sin sesión devuelve código 4 y mensaje en `stderr`; un recurso sin permiso devuelve 1 con
  cuerpo JSON `{"message": ...}`. Ambos se traducen a «no comprobada», con el mensaje.

## R7. Qué no se comprueba y por qué

Fuera de alcance por las aclaraciones 1 y 2 de la spec: ajustes de fusión y seguridad por repositorio
(guía §5) y permisos de equipos sobre repositorios (guía §6). Tampoco la pertenencia de personas a
equipos ni el contenido de los secretos.
