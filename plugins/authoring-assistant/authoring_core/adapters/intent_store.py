"""Se hace cargo de dónde vive la intención pendiente entre invocaciones.

En la configuración local del repositorio: no se versiona, no ensucia el árbol de trabajo y sobrevive
a cerrar la sesión. Es lo que permite retomar sin volver a preguntarlo todo.

Consecuencia que conviene saber: la configuración local es del repositorio, no del árbol de trabajo,
así que varios árboles del mismo repositorio comparten la intención. Y una copia nueva no la hereda,
porque la memoria no viaja con el código.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

KEY_ACTION = "authoring.pendingAction"
KEY_UNIT = "authoring.pendingUnit"
GIT_TIMEOUT_SECONDS = 30


def _config(args: list[str], cwd: Path | None = None) -> str:
    """Lo que git config responda, o cadena vacía si la clave no está.

    Que una clave no exista no es un fallo: es la respuesta «no hay nada pendiente».
    """
    try:
        completed = subprocess.run(
            ["git", "config", "--local", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=cwd,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def read(cwd: Path | None = None) -> tuple[str, str]:
    """La acción y la unidad guardadas, tal cual, sin juzgar si sirven."""
    return _config(["--get", KEY_ACTION], cwd), _config(["--get", KEY_UNIT], cwd)


def write(action: str, unit: str | None, cwd: Path | None = None) -> None:
    _config([KEY_ACTION, action], cwd)
    if unit:
        _config([KEY_UNIT, unit], cwd)
    else:
        _config(["--unset", KEY_UNIT], cwd)


def clear(cwd: Path | None = None) -> None:
    _config(["--unset", KEY_ACTION], cwd)
    _config(["--unset", KEY_UNIT], cwd)
