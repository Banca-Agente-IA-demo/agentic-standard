"""Dónde vive una unidad dentro del repositorio del autor.

El nombre de la unidad es el que declara su manifiesto, no el de su carpeta: los dos suelen coincidir
y no tienen por qué. Buscar por manifiesto es lo que hace que el asistente encuentre la unidad que el
autor nombró y no la que se le parece.
"""

from __future__ import annotations

import json
from pathlib import Path

from authoring_core.adapters.git import MANIFEST_GLOB, run_git


class UnitNotFound(LookupError):
    """En este repositorio no hay ninguna unidad con ese nombre."""


def root_of(unit: str, cwd: Path | None = None) -> Path:
    """La carpeta de la unidad, o un error de dominio si no está."""
    repository = Path(run_git(["rev-parse", "--show-toplevel"], cwd))
    for manifest in sorted(repository.glob(MANIFEST_GLOB)):
        if _declared_name(manifest) == unit:
            return manifest.parent.parent
    raise UnitNotFound(f"no hay ninguna unidad llamada {unit!r} en este repositorio")


def _declared_name(manifest: Path) -> str | None:
    try:
        return json.loads(manifest.read_text(encoding="utf-8"))["name"]
    except (json.JSONDecodeError, KeyError, TypeError, OSError):
        return None  # un manifiesto ilegible ya lo avisa la clasificación del estado
