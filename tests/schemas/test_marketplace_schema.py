"""El contrato del índice del marketplace: dos proyecciones, una por cliente.

Convertido de `check_marketplace` del `selfcheck.py` del paquete de diseño del hito 1. La divergencia
que estas pruebas protegen está medida: Copilot rechaza la fuente `git-subdir`, y Claude Code acepta
`github` con `path` pero lo ignora e instala el repositorio entero sin dar error (T3).
"""

from __future__ import annotations

import copy

from jsonschema import Draft202012Validator

from tests.schemas.conftest import load_fixture
from tests.support import errors_of

CLAUDE_INDEX = "marketplace-exp.claude-code.json"
COPILOT_INDEX = "marketplace-exp.copilot.json"


def test_el_indice_de_claude_pasa_su_proyeccion_con_version_con_sufijo(claude_validator):
    index = load_fixture(CLAUDE_INDEX)
    assert index["plugins"][0]["version"] == "0.2.0-beta.1"
    assert errors_of(claude_validator, index) == []


def test_el_indice_de_copilot_pasa_su_proyeccion_con_version_con_sufijo(copilot_validator):
    index = load_fixture(COPILOT_INDEX)
    assert index["plugins"][0]["version"] == "0.2.0-beta.1"
    assert errors_of(copilot_validator, index) == []


def test_la_fuente_github_con_path_es_error_en_la_proyeccion_de_claude(claude_validator):
    # Claude Code la acepta e ignora el path: instalaría el repositorio completo sin avisar.
    errors = errors_of(claude_validator, load_fixture(COPILOT_INDEX))
    assert any("is not valid under any" in e for e in errors)


def test_la_fuente_git_subdir_es_error_en_la_proyeccion_de_copilot(copilot_validator):
    # Copilot la rechaza, y una sola entrada así rompe el índice entero para ese cliente.
    errors = errors_of(copilot_validator, load_fixture(CLAUDE_INDEX))
    assert any("is not valid under any" in e for e in errors)


def test_un_indice_sin_unidades_es_error(claude_validator):
    # Salvaguarda medida: un índice vacío es sintácticamente válido y al publicarse desinstala de
    # golpe todo lo que ofrecía.
    bad = copy.deepcopy(load_fixture(CLAUDE_INDEX))
    bad["plugins"] = []
    assert any("non-empty" in e for e in errors_of(claude_validator, bad))


def test_metadatos_de_compilacion_en_la_version_de_una_unidad_es_error(claude_validator):
    bad = copy.deepcopy(load_fixture(CLAUDE_INDEX))
    bad["plugins"][0]["version"] = "0.2.0-beta.1+build.7"
    assert any("does not match" in e for e in errors_of(claude_validator, bad))


def test_la_version_del_propio_indice_no_admite_sufijo(claude_validator):
    # Las unidades sí lo admiten; el índice no, porque no se publica por canales.
    bad = copy.deepcopy(load_fixture(CLAUDE_INDEX))
    bad["metadata"]["version"] = "1.0.0-beta.1"
    assert any("does not match" in e for e in errors_of(claude_validator, bad))


def test_un_nombre_de_unidad_que_no_es_slug_es_error(claude_validator):
    bad = copy.deepcopy(load_fixture(CLAUDE_INDEX))
    bad["plugins"][0]["name"] = "CNF Migration Flow"
    assert any("does not match" in e for e in errors_of(claude_validator, bad))


def test_la_raiz_del_esquema_rechaza_todo_para_que_nadie_pase_en_vacio(marketplace_schema):
    # Un validador apuntado a la raíz por error validaría cualquier cosa si la raíz no impusiera nada.
    root = Draft202012Validator(marketplace_schema)
    errors = errors_of(root, load_fixture(CLAUDE_INDEX))
    assert any("should not be valid" in e for e in errors)
