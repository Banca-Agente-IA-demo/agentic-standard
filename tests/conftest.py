"""Validadores de los esquemas del estándar, disponibles para todas las pruebas del repositorio."""

from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator

from tests.support import build_validator, load_schema, projection_validator


@pytest.fixture(scope="session")
def governance_validator() -> Draft202012Validator:
    return build_validator(load_schema("governance.schema.json"))


@pytest.fixture(scope="session")
def marketplace_schema() -> dict:
    return load_schema("marketplace.schema.json")


@pytest.fixture(scope="session")
def claude_validator(marketplace_schema: dict) -> Draft202012Validator:
    return projection_validator(marketplace_schema, "claudeCode")


@pytest.fixture(scope="session")
def copilot_validator(marketplace_schema: dict) -> Draft202012Validator:
    return projection_validator(marketplace_schema, "copilot")
