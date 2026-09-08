"""Los lanzamientos publicados, preguntados a la herramienta de GitHub.

Es la única implementación del único puerto, y lo único del asistente que necesita red. Por eso el
puerto existe: con un doble, las reglas se prueban sin salir de la máquina.
"""

from __future__ import annotations

import json
import logging
import subprocess

from authoring_core.domain.release_tags import Release

GH_TIMEOUT_SECONDS = 60
# Tope de lanzamientos que se piden. La versión más alta está entre los recientes, y pedirlos todos
# en un repositorio con años de historia es lento sin cambiar el resultado.
MAX_RELEASES = 100

log = logging.getLogger(__name__)


class ReleasesUnavailable(RuntimeError):
    """No se pudo preguntar por los lanzamientos: falta la herramienta, o no hay acceso."""


class GitHubReleases:
    """Los lanzamientos del repositorio donde se ejecuta."""

    def list_releases(self, unit: str) -> tuple[Release, ...]:
        """Todos los del repositorio. De cuáles son de esta unidad se encarga el dominio."""
        log.debug("pidiendo los lanzamientos para la unidad %s", unit)
        return _parse(_ask_github())


def _ask_github() -> str:
    try:
        completed = subprocess.run(
            ["gh", "release", "list", "--limit", str(MAX_RELEASES), "--json", "tagName,isDraft"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=GH_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as failure:
        raise ReleasesUnavailable(str(failure)) from failure
    if completed.returncode != 0:
        lines = (completed.stderr or "").strip().splitlines()
        raise ReleasesUnavailable(lines[-1] if lines else "no se pudo consultar los lanzamientos")
    return completed.stdout


def _parse(raw: str) -> tuple[Release, ...]:
    try:
        entries = json.loads(raw or "[]")
    except json.JSONDecodeError as failure:
        raise ReleasesUnavailable(f"respuesta ilegible al pedir los lanzamientos: {failure}") from failure
    return tuple(
        Release(tag=entry["tagName"], is_draft=bool(entry.get("isDraft")))
        for entry in entries
        if isinstance(entry, dict) and entry.get("tagName")
    )
