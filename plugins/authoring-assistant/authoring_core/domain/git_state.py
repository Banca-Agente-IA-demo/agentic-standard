"""Se hace cargo de clasificar en qué estado está el repositorio del autor.

Puro: recibe lo observado y devuelve el estado. Quien ejecuta git es un adaptador, así que estas
reglas se prueban con datos y sin repositorio (T1).

El asistente es de autoría, no de git: sólo sigue desde la rama principal limpia o desde una rama de
trabajo limpia. Todo lo demás se detiene con el mensaje de qué corregir, sin ejecutar nada, y antes de
preguntar nada, que es cuando detenerse no pierde trabajo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

MAIN_BRANCH = "main"

# Los nombres de estado son contrato: el modelo lee este campo y no interpreta la salida de git.
STATE_MAIN_CLEAN = "main_clean"
STATE_WORK_BRANCH_CLEAN = "work_branch_clean"
STATE_DIRTY = "dirty"
STATE_UNKNOWN_BRANCH = "unknown_branch"
STATE_UNIT_NOT_FOUND = "unit_not_found"
STATE_BLOCKED = "blocked"


class Action(str, Enum):
    """Lo que el prefijo de la rama declara que se está haciendo."""

    CREATE = "feat"
    MODIFY = "fix"
    DEPRECATE = "deprecate"


# Forma del nombre de rama: `<accion>/<unidad>`, con la unidad en minúsculas y guiones.
BRANCH_PATTERN = re.compile(rf"^({'|'.join(a.value for a in Action)})/([a-z0-9][a-z0-9-]*)$")


@dataclass(frozen=True)
class WorkBranch:
    action: Action
    unit: str


def parse_branch(branch: str) -> WorkBranch | None:
    """La acción y la unidad que el nombre declara, o `None` si no tiene la forma esperada."""
    match = BRANCH_PATTERN.match(branch)
    if match is None:
        return None
    return WorkBranch(action=Action(match.group(1)), unit=match.group(2))


@dataclass(frozen=True)
class Observation:
    """Lo que el adaptador de git ve. Nada de esto se decide aquí, sólo se recibe."""

    branch: str
    is_dirty: bool
    units: tuple[str, ...] = ()
    blocked_reason: str | None = None
    """Operación a medias, cabeza suelta o falta de origen, ya redactada por quien la observó."""
    behind_remote: bool = False
    """La rama principal está por detrás de su origen."""
    behind_main: bool = False
    """La rama de trabajo está por detrás de la principal."""
    unreadable_manifests: tuple[str, ...] = field(default_factory=tuple)
    """Manifiestos que no se pudieron leer. No pueden desaparecer en silencio: su unidad faltaría de
    la lista y el asistente diría que no existe, que es el peor mensaje posible."""


@dataclass(frozen=True)
class GitState:
    state: str
    branch: str
    message: str | None = None
    action: Action | None = None
    unit: str | None = None
    units: tuple[str, ...] = ()
    behind_remote: bool = False
    behind_main: bool = False
    unreadable_manifests: tuple[str, ...] = field(default_factory=tuple)

    @property
    def can_continue(self) -> bool:
        return self.state in (STATE_MAIN_CLEAN, STATE_WORK_BRANCH_CLEAN)


def classify(observation: Observation) -> GitState:
    """El estado del repositorio, con lo que el diálogo necesita de cada uno."""
    common = {
        "branch": observation.branch,
        "unreadable_manifests": observation.unreadable_manifests,
    }
    if observation.blocked_reason:
        return GitState(
            state=STATE_BLOCKED,
            message=(
                f"Resuelve el estado del repositorio ({observation.blocked_reason}; `git status` lo "
                "describe) y vuelve a invocar al asistente."
            ),
            **common,
        )

    work = parse_branch(observation.branch)

    if observation.is_dirty:
        retake = " Si la rama es <accion>/<unidad>, retomará esa unidad." if work else ""
        return GitState(
            state=STATE_DIRTY,
            message=(
                f"Hay cambios sin guardar en `{observation.branch}`. Haz commit de lo que ya está "
                "escrito, o guárdalo con `git stash`, y vuelve a invocar al asistente." + retake
            ),
            **common,
        )

    if observation.branch == MAIN_BRANCH:
        return GitState(
            state=STATE_MAIN_CLEAN,
            units=observation.units,
            behind_remote=observation.behind_remote,
            **common,
        )

    if work is None:
        return GitState(
            state=STATE_UNKNOWN_BRANCH,
            message=(
                f"Estás en `{observation.branch}`. El asistente trabaja desde `main` o desde una rama "
                "`feat/`, `fix/` o `deprecate/` seguida del nombre de la unidad. Cámbiate a `main` "
                "(`git switch main`) o renombra la rama (`git branch -m <accion>/<unidad>`) y vuelve "
                "a invocar al asistente."
            ),
            **common,
        )

    # En una rama de creación la unidad puede no existir todavía: es la que se está creando.
    if work.action is not Action.CREATE and work.unit not in observation.units:
        existing = ", ".join(observation.units) or "ninguna"
        return GitState(
            state=STATE_UNIT_NOT_FOUND,
            message=(
                f"`{observation.branch}`: no hay ninguna unidad `{work.unit}` en este repositorio. "
                f"Las unidades son: {existing}."
            ),
            units=observation.units,
            **common,
        )

    return GitState(
        state=STATE_WORK_BRANCH_CLEAN,
        action=work.action,
        unit=work.unit,
        units=observation.units,
        behind_main=observation.behind_main,
        **common,
    )
