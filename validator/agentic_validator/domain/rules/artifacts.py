"""Los artefactos de texto y su suite: lo poco que el estándar lee de formatos ajenos.

La estructura interna de cada tipo la fija la herramienta (04 §4). Aquí sólo se comprueba lo que la
sección 5 de la revisión enumera, más las dos reglas de portabilidad medidas en D7.
"""

from __future__ import annotations

from agentic_validator.domain.model import (
    DETERMINISTIC_ASSERT_TYPES,
    GOVERNANCE_FILE,
    MIN_EVAL_CASES,
    REQUIRED_EVAL_CATEGORIES,
    Finding,
    TextArtifact,
    UnitSnapshot,
    error,
    warning,
)

# Los siete campos de gobierno que la demo guardaba en el frontmatter y que hoy viven en otro sitio.
GOVERNANCE_FIELDS_IN_FRONTMATTER = frozenset(
    {"id", "owner_team", "owner_contact", "status", "version", "standard_version", "data_classification"}
)

# Las dos grafías con las que un agente restringe su servidor. Medido el 7 de septiembre de 2026 (D7):
# cada cliente ignora en silencio la que no entiende, así que hacen falta las dos.
CLAUDE_MCP_TOOL_PREFIX = "mcp__plugin_"
COPILOT_MCP_TOOL_SUFFIX = "/*"

# C3 aplica a lo que interpreta contenido externo: skill, prompt y agente (03 §3). Una unidad que sólo
# expone un servidor o unos hooks no lo interpreta.
_TYPES_REQUIRING_EXTERNAL_CONTENT = ("skills", "prompts", "agents")


def check_artifact_names(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El nombre declarado y el que impone la ruta tienen que coincidir.

    Si no coinciden, el cliente no encuentra el artefacto: no da error, simplemente no aparece.
    """
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        if artifact.error:
            findings.append(
                error("artifact.frontmatter-unreadable", artifact.path, f"no se pudo interpretar: {artifact.error}")
            )
            continue
        front = artifact.frontmatter
        if front is None:
            findings.append(error("artifact.frontmatter-missing", artifact.path, "el archivo no lleva frontmatter"))
            continue
        declared = front.get("name")
        if not declared:
            findings.append(error("artifact.name-missing", artifact.path, "el frontmatter no declara nombre"))
        elif str(declared) != artifact.expected_name:
            findings.append(
                error(
                    "artifact.name-mismatch",
                    artifact.path,
                    f"declara el nombre {declared!r} y su ruta impone {artifact.expected_name!r}",
                )
            )
    return tuple(findings)


def check_artifact_descriptions(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """La descripción es lo que el modelo lee para decidir si usa el artefacto (04 §1)."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        front = artifact.frontmatter
        if front is None:
            continue
        if not str(front.get("description") or "").strip():
            findings.append(error("artifact.description-missing", artifact.path, "el frontmatter no declara descripción"))
    return tuple(findings)


def check_no_governance_in_frontmatter(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El gobierno vive en su archivo; el frontmatter sólo lleva lo que el cliente lee (D1)."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        front = artifact.frontmatter or {}
        catalog = front.get("metadata")
        keys = set(front) | (set(catalog) if isinstance(catalog, dict) else set())
        leaked = sorted(GOVERNANCE_FIELDS_IN_FRONTMATTER & keys)
        if leaked:
            findings.append(
                error(
                    "artifact.governance-in-frontmatter",
                    artifact.path,
                    f"campos de gobierno en el frontmatter: {', '.join(leaked)}; viven en {GOVERNANCE_FILE}",
                )
            )
    return tuple(findings)


def check_catalog_metadata_is_text(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """D1: el mapa de catálogo es texto a texto, como define la especificación de skills."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        catalog = (artifact.frontmatter or {}).get("metadata")
        if not isinstance(catalog, dict):
            continue
        non_text = sorted(key for key, value in catalog.items() if not isinstance(value, str))
        if non_text:
            findings.append(
                error(
                    "artifact.catalog-not-text",
                    artifact.path,
                    f"el mapa metadata debe ser texto a texto y no lo es en: {', '.join(non_text)}",
                )
            )
    return tuple(findings)


def check_agent_mcp_spellings(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """D7: si el agente restringe su servidor, declara las dos grafías; si no restringe, avisa."""
    if not snapshot.has_mcp:
        return ()
    findings: list[Finding] = []
    for agent in snapshot.agents:
        tools = (agent.frontmatter or {}).get("tools")
        if not isinstance(tools, list):
            findings.append(
                warning(
                    "artifact.agent-inherits-everything",
                    agent.path,
                    "el agente no declara tools y hereda todo lo instalado en la sesión, que es lo contrario de C1",
                )
            )
            continue
        names = [str(tool) for tool in tools]
        has_claude = any(name.startswith(CLAUDE_MCP_TOOL_PREFIX) for name in names)
        has_copilot = any(name.endswith(COPILOT_MCP_TOOL_SUFFIX) and not name.startswith("mcp__") for name in names)
        if not has_claude and not has_copilot:
            continue
        if not has_claude:
            findings.append(
                error(
                    "artifact.agent-missing-claude-spelling",
                    agent.path,
                    "el agente restringe el servidor sólo con la grafía de Copilot; Claude rehúsa lanzarlo",
                )
            )
        if not has_copilot:
            findings.append(
                error(
                    "artifact.agent-missing-copilot-spelling",
                    agent.path,
                    "el agente restringe el servidor sólo con la grafía de Claude; Copilot lo arranca sin el servidor y no avisa",
                )
            )
    return tuple(findings)


def check_external_content_declared(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C3 se exige según el tipo de lo que la unidad contiene, no siempre."""
    governance = snapshot.governance
    if governance is None:
        return ()
    interprets_external = any(getattr(snapshot, kind) for kind in _TYPES_REQUIRING_EXTERNAL_CONTENT)
    if not interprets_external:
        return ()
    if not str(governance.get("external_content") or "").strip():
        return (
            error(
                "artifact.external-content-missing",
                GOVERNANCE_FILE,
                "la unidad lleva artefactos que interpretan contenido externo y no declara cómo lo trata",
            ),
        )
    return ()


def check_eval_suites(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """La suite no es obligatoria aquí, pero si la unidad la trae tiene que tener la forma exigida."""
    findings: list[Finding] = []
    for suite in snapshot.eval_suites:
        if suite.error:
            findings.append(error("evals.unreadable", suite.path, f"no se pudo interpretar: {suite.error}"))
            continue
        tests = (suite.content or {}).get("tests")
        if not isinstance(tests, list) or len(tests) < MIN_EVAL_CASES:
            findings.append(
                error("evals.too-few-cases", suite.path, f"la suite necesita al menos {MIN_EVAL_CASES} casos")
            )
            continue
        findings.extend(_check_suite_cases(suite.path, tests))
    return tuple(findings)


def _check_suite_cases(path: str, tests: list) -> list[Finding]:
    findings: list[Finding] = []
    categories: set[str] = set()
    for case in tests:
        metadata = case.get("metadata") if isinstance(case, dict) else None
        category = (metadata or {}).get("category") if isinstance(metadata, dict) else None
        description = (case.get("description") if isinstance(case, dict) else None) or "sin descripción"
        if category is None:
            findings.append(
                error("evals.case-without-category", path, f"el caso {description!r} no declara metadata.category")
            )
        else:
            categories.add(str(category))
        assertions = case.get("assert") if isinstance(case, dict) else None
        types = {a.get("type") for a in assertions} if isinstance(assertions, list) else set()
        if not types & DETERMINISTIC_ASSERT_TYPES:
            findings.append(
                error(
                    "evals.case-without-deterministic-assertion",
                    path,
                    f"el caso {description!r} sólo se sostiene en el juez; sin él no dice nada",
                )
            )
    missing = sorted(REQUIRED_EVAL_CATEGORIES - categories)
    if missing:
        findings.append(
            error("evals.missing-categories", path, f"la suite no cubre las categorías: {', '.join(missing)}")
        )
    return findings


def _artifact_kind(artifact: TextArtifact) -> str:
    return artifact.path.split("/", 1)[0]
