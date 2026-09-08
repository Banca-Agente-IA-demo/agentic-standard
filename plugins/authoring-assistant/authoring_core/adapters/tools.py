"""Se hace cargo de mirar qué hay instalado en la máquina del autor.

Sólo mira. Instalar o crear entornos es otra responsabilidad y llega con la capacidad que lo necesita.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from authoring_core.domain.tooling import MINIMUM_PYTHON, ToolObservation

TOOL_TIMEOUT_SECONDS = 30

PYTHON_FIX = (
    "Instala Python {minimum} o superior y asegúrate de que `python` lo encuentra en el PATH."
)
GIT_FIX = "Instala git y comprueba que `git --version` responde."
GH_FIX = "Instala gh y abre una sesión con `gh auth login`."


def _responds(command: list[str]) -> bool:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=TOOL_TIMEOUT_SECONDS, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _python() -> ToolObservation:
    minimum = ".".join(str(part) for part in MINIMUM_PYTHON)
    return ToolObservation(
        name="python",
        present=True,  # si esto se está ejecutando, hay un intérprete
        version=sys.version_info[:2],
        how_to_fix=PYTHON_FIX.format(minimum=minimum),
    )


def _git() -> ToolObservation:
    return ToolObservation(name="git", present=shutil.which("git") is not None, how_to_fix=GIT_FIX)


def _gh() -> ToolObservation:
    present = shutil.which("gh") is not None
    return ToolObservation(
        name="gh",
        present=present,
        # Estar instalada no basta: sin sesión no puede leer nada de la plataforma.
        authenticated=_responds(["gh", "auth", "status"]) if present else None,
        how_to_fix=GH_FIX,
    )


def observe() -> tuple[ToolObservation, ...]:
    return (_python(), _git(), _gh())
