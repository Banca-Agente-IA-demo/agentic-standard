"""Lee el diff de la unidad contra la rama principal del origen. Sólo lee.

El diff va acotado a la carpeta de la unidad: lo que se toque fuera no cuenta para su versión. Los
renombrados se piden partidos en una retirada y un alta, que es lo que son para quien consume la
unidad, así que no se activa la detección de renombrados de git.
"""

from __future__ import annotations

import json
from pathlib import Path

from authoring_core.adapters.git import GitUnavailable, run_git
from authoring_core.domain.diff_rules import GOVERNANCE_FILE, Change, FileChange

MAIN_REF = "origin/main"
_STATUS = {"A": Change.ADDED, "M": Change.MODIFIED, "D": Change.DELETED}


def read_changes(unit_root: Path, cwd: Path | None = None) -> tuple[FileChange, ...]:
    """Los archivos que el cambio toca dentro de la unidad, con qué les pasó."""
    relative = _relative_to_repository(unit_root, cwd)
    raw = run_git(["diff", "--name-status", "--no-renames", f"{MAIN_REF}...HEAD", "--", relative], cwd)
    changes: list[FileChange] = []
    for line in raw.splitlines():
        parsed = _parse_line(line, relative)
        if parsed is not None:
            changes.append(_with_keys(parsed, unit_root, relative, cwd))
    return tuple(changes)


def _parse_line(line: str, unit_prefix: str) -> FileChange | None:
    """Una línea de estado y ruta, con la ruta ya relativa a la raíz de la unidad."""
    status, _, path = line.partition("\t")
    change = _STATUS.get(status.strip()[:1])
    if change is None or not path:
        return None
    inside = path.strip()[len(unit_prefix) :].lstrip("/")
    return FileChange(path=inside, change=change) if inside else None


def _with_keys(change: FileChange, unit_root: Path, unit_prefix: str, cwd: Path | None) -> FileChange:
    """El gobierno necesita saber qué claves cambiaron, no sólo que el archivo cambió."""
    if change.path != GOVERNANCE_FILE or change.change is Change.DELETED:
        return change
    before = _governance_at(MAIN_REF, f"{unit_prefix}/{GOVERNANCE_FILE}", cwd)
    after = _governance_now(unit_root / GOVERNANCE_FILE)
    touched = tuple(sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)))
    return FileChange(path=change.path, change=change.change, touched_keys=touched)


def _governance_at(ref: str, path: str, cwd: Path | None) -> dict:
    try:
        return _as_object(run_git(["show", f"{ref}:{path}"], cwd))
    except GitUnavailable:
        return {}  # no existía en la rama principal: todo lo que tenga ahora es nuevo


def _governance_now(path: Path) -> dict:
    try:
        return _as_object(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def _as_object(text: str) -> dict:
    try:
        content = json.loads(text)
    except json.JSONDecodeError:
        # Un gobierno corrupto lo dice el validador con su mensaje; aquí sólo significa que no se
        # puede afinar por claves, y el archivo cuenta igual como tocado.
        return {}
    return content if isinstance(content, dict) else {}


def _relative_to_repository(unit_root: Path, cwd: Path | None) -> str:
    root = Path(run_git(["rev-parse", "--show-toplevel"], cwd))
    return unit_root.resolve().relative_to(root.resolve()).as_posix()
