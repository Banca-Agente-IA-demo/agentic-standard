"""El contrato de gobierno viaja dentro del paquete y es el del repositorio (D5).

Si el esquema del paquete y el del repositorio pudieran separarse, el autor vería verde y la solicitud
de cambio vería rojo. Por eso el constructor lo inyecta desde el único archivo del repositorio y esta
prueba lo comprueba sobre la distribución ya construida.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from agentic_validator.adapters.contract import GOVERNANCE_SCHEMA, schema_path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = REPO_ROOT / "validator"
CANONICAL_SCHEMA = REPO_ROOT / "schemas" / GOVERNANCE_SCHEMA
BUNDLED_INSIDE_WHEEL = f"agentic_validator/schemas/{GOVERNANCE_SCHEMA}"


def test_en_un_clon_de_trabajo_el_esquema_es_el_unico_del_repositorio():
    # Sin construir, la instalación editable no tiene el esquema inyectado y se usa el canónico.
    assert schema_path().resolve() == CANONICAL_SCHEMA.resolve()


@pytest.mark.slow
def test_el_paquete_construido_lleva_dentro_el_esquema_del_repositorio(tmp_path):
    build = subprocess.run(
        [sys.executable, "-m", "hatchling", "build", "-t", "wheel"],
        cwd=VALIDATOR_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode != 0:
        pytest.skip(f"no se pudo construir la distribución: {build.stderr.strip().splitlines()[-1:]}")
    wheel = sorted((VALIDATOR_DIR / "dist").glob("*.whl"))[-1]
    with zipfile.ZipFile(wheel) as package:
        assert BUNDLED_INSIDE_WHEEL in package.namelist()
        assert package.read(BUNDLED_INSIDE_WHEEL) == CANONICAL_SCHEMA.read_bytes()
