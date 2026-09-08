"""Qué salto de versión exige un cambio, según la tabla de las reglas de versión.

La tabla del documento tiene tres filas: lo que cambia lo que la unidad puede hacer o a qué accede es
mayor, lo que añade capacidad es menor, y el resto es parche. Aquí hay una cuarta, y es una decisión
de esta capacidad, no del documento: **retirar** capacidad es mayor. La tabla sólo cubría añadir y
cambiar, así que un artefacto borrado caía por descarte en la última fila y salía como parche, aunque
rompa a quien lo invoca. Está anotado en las clarificaciones de la spec 008.

Puro: recibe el diff ya leído y devuelve la clasificación. No sabe qué es git.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

GOVERNANCE_FILE = "GOVERNANCE.json"
MCP_FILE = ".mcp.json"
MANIFEST_PATH = ".claude-plugin/plugin.json"
HOOKS_DIR = "hooks/"
EVALS_DIR = "evals/"

# Las carpetas cuyo contenido es capacidad que la unidad ofrece: añadir una es más capacidad, quitarla
# es menos, y las dos cosas le importan a quien la consume.
ARTIFACT_DIRECTORIES = ("skills/", "agents/", "commands/")

# Las claves del gobierno que dicen lo que la unidad puede hacer y a qué accede. Tocarlas obliga al
# aprobador a mirar otra vez.
GOVERNING_KEYS = ("permissions", "risk_level", "data_classification")


class Level(str, Enum):
    """Los tres saltos, de mayor a menor. El orden de declaración es el de precedencia."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


_PRECEDENCE = (Level.MAJOR, Level.MINOR, Level.PATCH)


class Change(str, Enum):
    """Qué le pasó a un archivo en el diff."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True)
class FileChange:
    """Un archivo del diff, con su ruta relativa a la raíz de la unidad."""

    path: str
    change: Change
    touched_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class Reason:
    """Por qué el salto es el que es: la ruta, la clave si la hay, y qué fila la señala."""

    level: Level
    path: str
    explanation: str
    key: str | None = None


@dataclass(frozen=True)
class DiffClassification:
    """El nivel mínimo que exige el cambio, con todo lo que lo justifica."""

    minimum: Level | None
    reasons: tuple[Reason, ...]
    is_empty: bool

    @property
    def touches_governance(self) -> bool:
        return any(reason.level is Level.MAJOR for reason in self.reasons)


def classify_changes(changes: tuple[FileChange, ...]) -> DiffClassification:
    """El nivel mínimo del cambio completo: manda la fila más alta, y constan todas."""
    if not changes:
        return DiffClassification(minimum=None, reasons=(), is_empty=True)
    reasons = tuple(reason for change in changes for reason in _reasons_for(change))
    if not reasons:
        return DiffClassification(minimum=None, reasons=(), is_empty=True)
    return DiffClassification(minimum=_highest(reasons), reasons=reasons, is_empty=False)


def _highest(reasons: tuple[Reason, ...]) -> Level:
    levels = {reason.level for reason in reasons}
    return next(level for level in _PRECEDENCE if level in levels)


def _reasons_for(change: FileChange) -> tuple[Reason, ...]:
    """Todas las filas de la tabla en las que cae un archivo. Puede caer en más de una."""
    if change.path == MANIFEST_PATH:
        # La versión vive aquí, así que el archivo cambia en cada salto: contarlo sería circular.
        return ()
    if _is_artifact(change.path):
        return (_artifact_reason(change),)
    if change.path == GOVERNANCE_FILE:
        return _governance_reasons(change)
    if change.path == MCP_FILE or change.path.startswith(HOOKS_DIR):
        return (
            Reason(
                level=Level.MAJOR,
                path=change.path,
                explanation="cambia a qué accede la unidad o qué ejecuta; el aprobador vuelve a mirar",
            ),
        )
    return (Reason(level=Level.PATCH, path=change.path, explanation=_ordinary_explanation(change)),)


def _artifact_reason(change: FileChange) -> Reason:
    if change.change is Change.DELETED:
        return Reason(
            level=Level.MAJOR,
            path=change.path,
            explanation="retira capacidad de una unidad publicada: quien la invoca deja de encontrarla",
        )
    if change.change is Change.ADDED:
        return Reason(
            level=Level.MINOR,
            path=change.path,
            explanation="añade capacidad sin quitar la que había",
        )
    return Reason(
        level=Level.PATCH,
        path=change.path,
        explanation="cambia el texto de un artefacto que ya estaba",
    )


def _governance_reasons(change: FileChange) -> tuple[Reason, ...]:
    governing = tuple(key for key in change.touched_keys if key in GOVERNING_KEYS)
    if not governing:
        return (
            Reason(
                level=Level.PATCH,
                path=change.path,
                explanation="cambia el gobierno sin tocar lo que la unidad puede hacer",
            ),
        )
    return tuple(
        Reason(
            level=Level.MAJOR,
            path=change.path,
            key=key,
            explanation="cambia lo que la unidad puede hacer o a qué accede; el aprobador vuelve a mirar",
        )
        for key in governing
    )


def _ordinary_explanation(change: FileChange) -> str:
    if change.change is Change.DELETED:
        return "quita un archivo que no es un artefacto: no había capacidad que retirar"
    if change.path.startswith(EVALS_DIR):
        return "cambia la suite de evaluación, que no altera lo que la unidad ofrece"
    return "no añade capacidad ni rompe la que había"


def _is_artifact(path: str) -> bool:
    return path.startswith(ARTIFACT_DIRECTORIES)
