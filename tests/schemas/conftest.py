"""Carga de los esquemas del estándar y construcción de sus validadores.

Es lo único compartido entre las pruebas del contrato de gobierno y las del índice del marketplace.
Todo lo demás son datos y aserciones (T1).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture(name: str) -> dict:
    return load_json(FIXTURES_DIR / name)


def errors_of(validator: Draft202012Validator, instance: dict) -> list[str]:
    """Mensajes de error con la ruta del campo delante, para poder afirmar por qué falló."""
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<raíz>'}: {error.message}"
        for error in validator.iter_errors(instance)
    ]


@pytest.fixture(scope="session")
def governance_validator() -> Draft202012Validator:
    schema = load_json(SCHEMAS_DIR / "governance.schema.json")
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture(scope="session")
def marketplace_schema() -> dict:
    return load_json(SCHEMAS_DIR / "marketplace.schema.json")


def projection_validator(schema: dict, projection: str) -> Draft202012Validator:
    """El esquema del índice se referencia por proyección: la raíz rechaza todo a propósito."""
    subschema = {**schema["projections"][projection], "$defs": schema["$defs"]}
    return Draft202012Validator(subschema, format_checker=FormatChecker())


@pytest.fixture(scope="session")
def claude_validator(marketplace_schema: dict) -> Draft202012Validator:
    return projection_validator(marketplace_schema, "claudeCode")


@pytest.fixture(scope="session")
def copilot_validator(marketplace_schema: dict) -> Draft202012Validator:
    return projection_validator(marketplace_schema, "copilot")


@pytest.fixture()
def complete_governance() -> dict:
    """Unidad agrupada completa: riesgo, permisos, contenido externo y bloque mcp."""
    return load_fixture("governance-plugin-with-mcp.json")


@pytest.fixture()
def minimal_governance() -> dict:
    """Unidad individual mínima, obsoleta y sin sucesor."""
    return load_fixture("governance-individual-deprecated.json")
