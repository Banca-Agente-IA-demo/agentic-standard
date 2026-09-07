"""Validación del archivo de gobierno contra su contrato.

Es un adaptador y no una regla: carga el esquema que viaja dentro del paquete. D5 fija que el esquema
existe en un único sitio del repositorio y llega aquí inyectado al construir la distribución, así que
la automatización y el editor validan contra el mismo archivo.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from agentic_validator.domain.model import GOVERNANCE_FILE, Finding, error

GOVERNANCE_SCHEMA = "governance.schema.json"

# Dentro de la distribución instalada, el esquema viaja en la raíz del paquete, no en esta capa: es un
# dato del paquete, no de los adaptadores. La ruta tiene que coincidir con la que el constructor
# declara en `validator/pyproject.toml`, y hay una prueba que lo comprueba sobre el paquete construido.
BUNDLED_SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"
# En un clon de trabajo con instalación editable, la inyección del constructor no ha ocurrido y el
# esquema sólo está en su único sitio del repositorio. Es la misma ruta que el constructor copia, así
# que las dos formas de ejecutar validan contra el mismo archivo.
CHECKOUT_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


class SchemaNotFoundError(FileNotFoundError):
    """Ni la distribución ni el clon de trabajo tienen el contrato de gobierno."""


def schema_path() -> Path:
    for directory in (BUNDLED_SCHEMAS_DIR, CHECKOUT_SCHEMAS_DIR):
        candidate = directory / GOVERNANCE_SCHEMA
        if candidate.is_file():
            return candidate
    raise SchemaNotFoundError(
        f"no se encontró {GOVERNANCE_SCHEMA} ni en {BUNDLED_SCHEMAS_DIR} ni en {CHECKOUT_SCHEMAS_DIR}"
    )


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def check_against_contract(governance: dict | None) -> tuple[Finding, ...]:
    """Los hallazgos del contrato, con la ruta del campo delante del motivo."""
    if governance is None:
        return ()
    return tuple(
        error(
            "contract.governance",
            GOVERNANCE_FILE,
            f"{'/'.join(str(part) for part in failure.absolute_path) or '<raíz>'}: {failure.message}",
        )
        for failure in _validator().iter_errors(governance)
    )
