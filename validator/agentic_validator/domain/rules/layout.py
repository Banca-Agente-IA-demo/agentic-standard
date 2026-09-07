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
from agentic_validator.domain.standard import GOVERNANCE_FILE, HOOK_TESTS_DIR

# Carpetas que el árbol de 04 §4 reserva dentro de una unidad, con la marca por la que se reconoce un
# artefacto de ese tipo. Lo demás en la raíz es contenido de apoyo y no se juzga.
ARTIFACT_DIRECTORIES = {
    "skills": ("SKILL.md",),
    "agents": (".agent.md",),
    "commands": (".prompt.md",),
}


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
            continue  # una unidad individual lleva su único artefacto en la raíz (04 §4)
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


