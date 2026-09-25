"""Layout de la unidad según el árbol de 04 §4.

El estándar fija dónde vive cada tipo dentro de la unidad; la estructura interna de cada tipo la fija
la especificación de la herramienta. Un artefacto fuera de su sitio no falla al instalar: el cliente
sencillamente no lo encuentra.

La higiene del contenido versionado, que también mira el árbol pero juzga lo que hay DENTRO de los
archivos, vive en `hygiene.py`.
"""

from __future__ import annotations

from agentic_validator.domain.findings import Finding, error
from agentic_validator.domain.snapshot import UnitSnapshot
from agentic_validator.domain.standard import GOVERNANCE_FILE, HOOK_TESTS_DIR, MCP_FILE

# Carpetas que el árbol de 04 §4 reserva dentro de una unidad, con la marca por la que se reconoce un
# artefacto de ese tipo. Lo demás en la raíz es contenido de apoyo y no se juzga.
ARTIFACT_DIRECTORIES = {
    "skills": ("SKILL.md",),
    "agents": (".agent.md",),
    "commands": (".prompt.md",),
}

# Los DOS únicos artefactos que viven en la raíz de la unidad, y sólo en la forma individual.
#
# Medido el 16 de septiembre de 2026 en Claude Code 2.1.272 y Copilot CLI 1.0.85, experimento 6: un
# `.agent.md`, un `.prompt.md` o un `hooks.json` en la raíz de la unidad **instalan con mensaje de
# éxito y no cargan nada** (`Agents (0)`, `Hooks (0)`, ausentes del listado de Copilot). Sólo el
# `SKILL.md` se carga desde la raíz en los dos clientes, y el `.mcp.json` vive ahí también en la forma
# agrupada. Todo lo demás necesita su subcarpeta.
ARTIFACTS_ALLOWED_AT_ROOT = frozenset({"SKILL.md", MCP_FILE})


def check_no_nested_unit(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El envoltorio de gobierno vive sólo en la raíz: una unidad no contiene a otra."""
    nested = [path for path in snapshot.files if path != GOVERNANCE_FILE and path.endswith("/" + GOVERNANCE_FILE)]
    return tuple(
        error(
            "layout.nested-unit",
            path,
            f"{GOVERNANCE_FILE} sólo vive en la raíz de la unidad; una unidad no contiene a otra",
        )
        for path in nested
    )


def check_artifacts_are_in_their_directory(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Un archivo de artefacto fuera de su carpeta no lo encuentra el cliente, y no da error."""
    findings: list[Finding] = []
    for path in snapshot.files:
        if "/" not in path:
            if path in ARTIFACTS_ALLOWED_AT_ROOT:
                continue
            findings.extend(_artifact_at_root_finding(path))
            continue
        directory = path.split("/", 1)[0]
        for expected, markers in ARTIFACT_DIRECTORIES.items():
            if any(path.endswith(marker) for marker in markers) and directory != expected:
                findings.append(
                    error(
                        "layout.artifact-outside-its-directory",
                        path,
                        f"un artefacto de este tipo vive en {expected}/ dentro de la unidad",
                    )
                )
    return tuple(findings)


def _artifact_at_root_finding(path: str) -> tuple[Finding, ...]:
    """Un artefacto aplanado en la raíz de una unidad individual: instala y no carga."""
    for expected, markers in ARTIFACT_DIRECTORIES.items():
        if any(path.endswith(marker) for marker in markers):
            return (
                error(
                    "layout.artifact-flattened-at-root",
                    path,
                    f"un artefacto de este tipo vive en {expected}/ también cuando la unidad es "
                    "individual; en la raíz instala sin cargar y ningún cliente avisa",
                ),
            )
    if path == "hooks.json":
        return (
            error(
                "layout.artifact-flattened-at-root",
                path,
                "los hooks viven en hooks/hooks.json también cuando la unidad es individual; "
                "en la raíz Claude Code no los registra y no avisa",
            ),
        )
    return ()


def check_hooks_bring_tests(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C5: los hooks traen pruebas que ejercitan su script con entrada y salida observables."""
    if not snapshot.has_hooks:
        return ()
    if any(path.startswith(HOOK_TESTS_DIR + "/") for path in snapshot.files):
        return ()
    return (
        error(
            "layout.hooks-without-tests",
            HOOK_TESTS_DIR,
            "la unidad ejecuta código propio sin que nadie lo invoque y no trae pruebas que lo ejerciten",
        ),
    )


