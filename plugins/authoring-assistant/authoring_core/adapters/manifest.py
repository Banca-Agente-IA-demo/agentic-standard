"""El manifiesto de la unidad: de dónde se lee la versión y dónde se escribe.

La versión vive aquí y en ningún otro sitio. Antes de escribir se comprueba que el destino está bajo
la raíz de la unidad elegida, que es la regla que impide que el asistente toque nada de fuera.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = ".claude-plugin/plugin.json"
VERSION_KEY = "version"
INDENT = 2


class ManifestError(ValueError):
    """El manifiesto no está, no se puede leer, o el destino no es de la unidad."""


def path_of(unit_root: Path) -> Path:
    return unit_root / MANIFEST_PATH


def read_version(unit_root: Path) -> str | None:
    """La versión declarada, o `None` si el manifiesto no la declara."""
    return _read(unit_root).get(VERSION_KEY)


def write_version(unit_root: Path, version: str) -> Path:
    """Escribe la versión en el manifiesto de esa unidad y devuelve el archivo que cambió."""
    manifest = path_of(unit_root)
    _refuse_outside(manifest, unit_root)
    content = _read(unit_root)
    updated = {**content, VERSION_KEY: version}
    manifest.write_text(json.dumps(updated, ensure_ascii=False, indent=INDENT) + "\n", encoding="utf-8")
    return manifest


def _refuse_outside(destination: Path, unit_root: Path) -> None:
    if not destination.resolve().is_relative_to(unit_root.resolve()):
        raise ManifestError(f"el destino {destination} no está bajo la unidad {unit_root}")


def _read(unit_root: Path) -> dict:
    manifest = path_of(unit_root)
    try:
        content = json.loads(manifest.read_text(encoding="utf-8"))
    except FileNotFoundError as failure:
        raise ManifestError(f"la unidad no tiene manifiesto en {MANIFEST_PATH}") from failure
    except json.JSONDecodeError as failure:
        raise ManifestError(f"el manifiesto no es JSON válido: {failure}") from failure
    except OSError as failure:
        raise ManifestError(f"no se pudo leer el manifiesto: {failure}") from failure
    if not isinstance(content, dict):
        raise ManifestError("el manifiesto no es un objeto")
    return content
