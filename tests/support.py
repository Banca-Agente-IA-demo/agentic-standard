"""Utilidades compartidas por las pruebas del estándar: carga de esquemas y lectura de errores.

Se extrajo de `tests/schemas/conftest.py` al aparecer el segundo consumidor, las pruebas de plantillas
(P9). Aquí van funciones puras; los fixtures viven en los `conftest.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> dict:
    return load_json(SCHEMAS_DIR / name)


def build_validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(schema, format_checker=FormatChecker())


def projection_validator(marketplace_schema: dict, projection: str) -> Draft202012Validator:
    """El esquema del índice se referencia por proyección: su raíz rechaza todo a propósito."""
    subschema = {**marketplace_schema["projections"][projection], "$defs": marketplace_schema["$defs"]}
    return build_validator(subschema)


def errors_of(validator: Draft202012Validator, instance: dict) -> list[str]:
    """Mensajes de error con la ruta del campo delante, para poder afirmar por qué falló."""
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<raíz>'}: {error.message}"
        for error in validator.iter_errors(instance)
    ]
