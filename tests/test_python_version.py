"""La versión mínima de Python se declara en un solo sitio y todo lo demás la sigue.

Estaba escrita en tres: el archivo de versión, el requisito del paquete del validador y la matriz de
CI. Tres copias de un número es la forma más barata de que se separen sin que nadie lo note.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION_FILE = REPO_ROOT / ".python-version"
VALIDATOR_PYPROJECT = REPO_ROOT / "validator" / "pyproject.toml"
ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"
TESTS_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tests.yml"


def declared_floor() -> str:
    """El único sitio donde vive el número; lo lee la composite action del registro."""
    return PYTHON_VERSION_FILE.read_text(encoding="utf-8").strip()


def _requires_python(pyproject: Path) -> str:
    match = re.search(r'^requires-python\s*=\s*"[><=]*([0-9.]+)"', pyproject.read_text(encoding="utf-8"), re.M)
    assert match, f"{pyproject.name} no declara requires-python"
    return match.group(1)


def test_el_archivo_de_version_declara_una_version_reconocible():
    assert re.fullmatch(r"\d+\.\d+", declared_floor()), declared_floor()


def test_los_dos_paquetes_declaran_el_mismo_suelo_que_el_archivo_de_version():
    for pyproject in (VALIDATOR_PYPROJECT, ROOT_PYPROJECT):
        assert _requires_python(pyproject) == declared_floor(), pyproject.name


def test_la_matriz_de_ci_prueba_el_suelo_declarado():
    # La matriz prueba dos versiones a propósito: el suelo, que protege al asistente en las máquinas
    # de BCP, y la de desarrollo. Si el suelo cambia y la matriz no, nadie vuelve a probarlo.
    matriz = re.search(r'python-version:\s*\[([^\]]+)\]', TESTS_WORKFLOW.read_text(encoding="utf-8"))
    assert matriz, "el workflow de pruebas no declara una matriz de versiones"
    versiones = [v.strip().strip('"') for v in matriz.group(1).split(",")]
    assert declared_floor() in versiones, versiones
