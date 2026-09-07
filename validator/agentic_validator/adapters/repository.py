"""Lo que hay que preguntarle a git y al árbol para saber qué unidades se tocaron.

Sólo lectura. El validador no cambia de rama, no confirma nada y no toca el trabajo de nadie: eso es
del asistente de autoría, y con reglas mucho más estrictas.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_validator.domain.standard import GOVERNANCE_FILE

log = logging.getLogger(__name__)

# Un diff de tres puntos compara con el ancestro común, que es lo que el autor entiende por «lo que he
# cambiado yo»: no le atribuye lo que otros hayan metido en la rama base mientras trabajaba.
_MERGE_BASE_RANGE = "{base}...HEAD"
_GIT_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class ChangedPaths:
    """Las rutas cambiadas, o el motivo por el que no se pudieron averiguar.

    `unavailable` no es un error del autor: en el primer push de una rama puede no haber punto de
    comparación. Quien decide qué hacer con eso es el caso de uso, no este adaptador.
    """

    paths: tuple[str, ...] = ()
    unavailable: str | None = None


def changed_paths(repository: Path, base: str, runner=subprocess.run) -> ChangedPaths:
    """Rutas relativas que cambiaron entre el ancestro común con `base` y el estado actual."""
    command = ["git", "-C", str(repository), "diff", "--name-only", _MERGE_BASE_RANGE.format(base=base)]
    try:
        completed = runner(
            command, capture_output=True, text=True, encoding="utf-8", check=False, timeout=_GIT_TIMEOUT_SECONDS
        )
    except (OSError, subprocess.SubprocessError) as failure:
        return ChangedPaths(unavailable=f"no se pudo ejecutar git: {failure}")
    if completed.returncode != 0:
        reason = (completed.stderr or "").strip().splitlines()
        return ChangedPaths(unavailable=reason[-1] if reason else f"git terminó con código {completed.returncode}")
    log.debug("%s -> %s rutas", " ".join(command), len(completed.stdout.splitlines()))
    return ChangedPaths(paths=tuple(line.strip() for line in completed.stdout.splitlines() if line.strip()))


def unit_roots(repository: Path) -> tuple[str, ...]:
    """Rutas relativas de toda carpeta que es una unidad publicable, por llevar su gobierno."""
    return tuple(
        sorted(
            path.parent.relative_to(repository).as_posix()
            for path in repository.rglob(GOVERNANCE_FILE)
            if path.is_file() and ".git" not in path.parts
        )
    )
