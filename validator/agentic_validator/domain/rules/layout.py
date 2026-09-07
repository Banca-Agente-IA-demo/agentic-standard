"""Layout de la unidad según el árbol de 04 §4, e higiene del contenido versionado (C2).

El estándar fija dónde vive cada tipo dentro de la unidad; la estructura interna de cada tipo la fija
la especificación de la herramienta. Un artefacto fuera de su sitio no falla al instalar: el cliente
sencillamente no lo encuentra.
"""

from __future__ import annotations

import re

from agentic_validator.domain.model import (
    GOVERNANCE_FILE,
    HOOK_TESTS_DIR,
    Finding,
    UnitSnapshot,
    error,
)

# Carpetas que el árbol de 04 §4 reserva dentro de una unidad, con la marca por la que se reconoce un
# artefacto de ese tipo. Lo demás en la raíz es contenido de apoyo y no se juzga.
ARTIFACT_DIRECTORIES = {
    "skills": ("SKILL.md",),
    "agents": (".agent.md",),
    "commands": (".prompt.md",),
}

# Una ruta absoluta versionada apunta a la máquina de quien la escribió. Se busca sólo en archivos
# ejecutables o de configuración: en la prosa de un README una ruta suele ser un ejemplo.
_ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'(=])(?:/(?:usr|home|opt|etc|var|tmp|Users)/|[A-Za-z]:[\\/])")
_EXECUTABLE_SUFFIXES = (".json", ".yaml", ".yml", ".sh", ".ps1", ".py", ".bat")


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


def check_no_absolute_paths(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C2: una ruta absoluta versionada sólo existe en la máquina de quien la escribió."""
    findings: list[Finding] = []
    for path, text in sorted(snapshot.text_contents.items()):
        if not path.endswith(_EXECUTABLE_SUFFIXES):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if _ABSOLUTE_PATH.search(line):
                findings.append(
                    error(
                        "hygiene.absolute-path",
                        f"{path}:{number}",
                        "hay una ruta absoluta; use ${CLAUDE_PLUGIN_ROOT} o una ruta relativa a la unidad",
                    )
                )
                break
    return tuple(findings)
