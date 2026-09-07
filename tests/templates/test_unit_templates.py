"""Las plantillas de unidad instanciadas cumplen el contrato de gobierno de la spec 002.

Convertido de la parte de plantillas de `check_governance` del `selfcheck.py` del paquete de diseño
del hito 1, más las reglas propias del archivo de identidad, que no tiene esquema a propósito.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.support import errors_of
from tests.templates.markers import MissingMarkerValue, STRUCTURED_TEMPLATES, instantiate, read_template

UNIT_TEMPLATES = ("plugin-unit", "individual-unit")

# El formato de plugin permite estos diez campos de primer nivel. El estándar no publica un esquema
# suyo (es formato ajeno), pero sí conserva la lista y exige version SemVer estricta, porque el índice
# la copia y la etiqueta debe coincidir con ella.
ALLOWED_PLUGIN_FIELDS = frozenset(
    {
        "$schema",
        "name",
        "version",
        "description",
        "author",
        "repository",
        "license",
        "keywords",
        "homepage",
        "category",
    }
)
STRICT_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(-(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?$"
)


@pytest.mark.parametrize("unit", UNIT_TEMPLATES)
def test_la_plantilla_de_gobierno_de_cada_unidad_valida_al_instanciarse(governance_validator, unit):
    governance = json.loads(instantiate(read_template(f"{unit}/GOVERNANCE.json")))
    assert errors_of(governance_validator, governance) == []


def test_el_bloque_del_servidor_mcp_encaja_en_la_plantilla_de_unidad_agrupada(governance_validator):
    # El bloque no es un archivo suelto: su instrucción dice que se pega en el gobierno de la unidad.
    governance = json.loads(instantiate(read_template("plugin-unit/GOVERNANCE.json")))
    block = json.loads(instantiate(read_template("artifacts/mcp/mcp-governance-block.json")))
    governance["permissions"] = {**governance["permissions"], "mcp_servers": ["jira"]}
    governance["mcp"] = block["mcp"]
    assert errors_of(governance_validator, governance) == []


@pytest.mark.parametrize("template", STRUCTURED_TEMPLATES)
def test_ninguna_plantilla_estructurada_deja_marcadores_sin_valor_de_prueba(template):
    # Un marcador sin cubrir viajaría hasta la unidad real como un valor plausible.
    assert instantiate(read_template(template))


@pytest.mark.parametrize("unit", UNIT_TEMPLATES)
def test_la_plantilla_de_identidad_de_cada_unidad_es_json_valido(unit):
    # Toda unidad lleva identidad, también la individual: no hay unidad suelta sin manifiesto.
    identity = json.loads(instantiate(read_template(f"{unit}/.claude-plugin/plugin.json")))
    assert identity["name"] and identity["description"]


@pytest.mark.parametrize("unit", UNIT_TEMPLATES)
def test_la_version_de_la_plantilla_de_identidad_es_semver_estricta(unit):
    identity = json.loads(instantiate(read_template(f"{unit}/.claude-plugin/plugin.json")))
    assert STRICT_SEMVER.match(identity["version"]), identity["version"]


@pytest.mark.parametrize("unit", UNIT_TEMPLATES)
def test_la_plantilla_de_identidad_no_declara_campos_fuera_del_formato(unit):
    identity = json.loads(instantiate(read_template(f"{unit}/.claude-plugin/plugin.json")))
    assert set(identity) <= ALLOWED_PLUGIN_FIELDS, sorted(set(identity) - ALLOWED_PLUGIN_FIELDS)


@pytest.mark.parametrize("unit", UNIT_TEMPLATES)
def test_el_nombre_de_identidad_y_la_segunda_mitad_del_id_de_gobierno_coinciden(unit):
    # rules lo exigirá sobre unidades reales; aquí se comprueba que la plantilla no nazca desalineada.
    identity = json.loads(instantiate(read_template(f"{unit}/.claude-plugin/plugin.json")))
    governance = json.loads(instantiate(read_template(f"{unit}/GOVERNANCE.json")))
    assert governance["id"].split("/", 1)[1] == identity["name"]


def test_la_plantilla_de_servidor_declara_exactamente_uno_y_con_la_misma_clave_que_su_gobierno():
    # D2: una unidad, un servidor. La clave de la conexión, la del bloque de gobierno y el único
    # elemento de los permisos tienen que ser la misma; si divergen, rules no puede emparejarlos.
    connection = json.loads(instantiate(read_template("artifacts/mcp/.mcp.json")))
    block = json.loads(instantiate(read_template("artifacts/mcp/mcp-governance-block.json")))
    assert len(connection["mcpServers"]) == 1
    assert set(connection["mcpServers"]) == set(block["mcp"])


def test_la_plantilla_de_servidor_referencia_la_credencial_por_nombre_y_no_por_valor():
    # C2: la unidad viaja sin el secreto; en la conexión sólo aparece el nombre de la variable.
    connection = json.loads(instantiate(read_template("artifacts/mcp/.mcp.json")))
    block = json.loads(instantiate(read_template("artifacts/mcp/mcp-governance-block.json")))
    declared = block["mcp"]["jira"]["credentials"]
    authorization = connection["mcpServers"]["jira"]["headers"]["Authorization"]
    assert all(f"${{{name}}}" in authorization for name in declared), authorization


def test_una_plantilla_con_un_marcador_desconocido_falla_al_instanciarse():
    with pytest.raises(MissingMarkerValue, match="INVENTADO"):
        instantiate('{"campo": "<<INVENTADO>>"}')
