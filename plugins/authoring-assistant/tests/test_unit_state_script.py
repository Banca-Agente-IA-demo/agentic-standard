"""El punto de entrada del estado de la unidad, sin red.

Pedir los lanzamientos de verdad sale a la red, así que aquí se comprueba lo que no depende de ello:
la forma del documento y el uso. El estado en sí ya está probado con datos.

El módulo se carga por su ruta y con un nombre propio: el script se llama igual que el módulo de
reglas, y importarlo sin más taparía a uno de los dos.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from authoring_core.domain.release_tags import Release
from authoring_core.domain.unit_state import classify

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "author-unit" / "scripts"
EXIT_COULD_NOT_RUN = 2
UNIT = "demo-unidad"


def _load_script():
    # El script encuentra lo suyo por su propia carpeta, igual que cuando lo lanza el cliente.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("unit_state_entry", SCRIPTS / "unit_state.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def script():
    return _load_script()


def test_el_documento_lleva_lo_que_el_dialogo_anuncia(script):
    documento = script.as_document(classify((Release(f"{UNIT}--v1.0.0", is_draft=False),), UNIT))
    assert documento["state"] == "production"
    assert documento["latest"] == "1.0.0"
    assert documento["has_final"] is True
    assert documento["can_be_deprecated"] is True


def test_en_desarrollo_el_documento_conserva_los_campos_en_falso(script):
    # Quitarlos por vacíos dejaría al modelo deduciendo lo que el documento debería decir.
    documento = script.as_document(classify((), UNIT))
    assert documento["has_final"] is False and documento["can_be_deprecated"] is False


def test_sin_el_nombre_de_la_unidad_se_dice_el_uso():
    resultado = subprocess.run(
        [sys.executable, str(SCRIPTS / "unit_state.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert resultado.returncode == EXIT_COULD_NOT_RUN
    assert "uso:" in resultado.stderr
    assert json.loads(resultado.stdout)["state"] == "unavailable"
