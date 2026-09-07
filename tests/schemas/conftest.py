"""Instancias de ejemplo que usan las pruebas de los esquemas.

Los validadores están en `tests/conftest.py`, porque los comparten las pruebas de plantillas.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support import load_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return load_json(FIXTURES_DIR / name)


@pytest.fixture()
def complete_governance() -> dict:
    """Unidad agrupada completa: riesgo, permisos, contenido externo y bloque mcp."""
    return load_fixture("governance-plugin-with-mcp.json")


@pytest.fixture()
def minimal_governance() -> dict:
    """Unidad individual mínima, obsoleta y sin sucesor."""
    return load_fixture("governance-individual-deprecated.json")
