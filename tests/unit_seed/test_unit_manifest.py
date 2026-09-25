"""El manifiesto sale de la plantilla, y lo único que el código añade es lo que no cabe en ella.

Pruebas de dominio puro: la plantilla se pasa ya parseada, así que ninguna toca disco (T1).
"""

from __future__ import annotations

import json

from unit_seed.unit_manifest import INITIAL_VERSION, build_manifest, build_mcp_config
from unit_seed.unit_request import UnitRequest

TEMPLATE = {
    "name": "<<NAME>>",
    "version": "<<VERSION>>",
    "description": "<<DESCRIPTION>>",
    "author": {"name": "<<TEAM>>", "email": "<<TEAM_MAILBOX>>"},
    "repository": "https://github.com/<<ORG>>/<<REPO>>",
    "license": "LicenseRef-BCP-Proprietary",
    "keywords": [],
    "metadata": {"governance": {"schema_version": "1.0", "risk_level": "<<RISK_LEVEL>>"}},
}

PAYLOAD = {
    "name": "cnf-migration-flow",
    "description": "Audita un microservicio Atlas y planifica su migracion a CNF.",
    "owner_team": "squad-cnf-migration",
    "team_mailbox": "squad-cnf-migration@bcp.com.pe",
    "risk_level": "medium",
    "unit_form": "grouped",
    "repository": "Banca-Agente-IA-demo/agents-modernization",
}


def _manifest(**extra: object) -> dict:
    return build_manifest(UnitRequest.model_validate({**PAYLOAD, **extra}), TEMPLATE)


def test_no_queda_ningun_marcador_sin_sustituir() -> None:
    # Un marcador sin cubrir viajaría hasta la unidad real y el autor lo vería como texto literal.
    assert "<<" not in json.dumps(_manifest())


def test_toda_unidad_nace_en_el_canal_experimental() -> None:
    # El sufijo de prelanzamiento decide el canal: sin él, la unidad entraría directa a producción
    # sin pasar por el piloto, que es justo lo que el ciclo de vida existe para impedir.
    assert _manifest()["version"] == INITIAL_VERSION
    assert "-beta." in INITIAL_VERSION


def test_el_gobierno_sale_de_la_plantilla_y_no_se_construye_en_el_codigo() -> None:
    # Cuando la plantilla no lo traía, la forma estaba escrita dos veces y podían divergir (C4).
    governance = _manifest()["metadata"]["governance"]
    assert governance == {"schema_version": "1.0", "risk_level": "medium"}


def test_sin_servidores_declarados_el_gobierno_no_lleva_bloque_mcp() -> None:
    # El bloque es obligatorio SI hay .mcp.json, y prohibido si no lo hay.
    assert "mcp" not in _manifest()["metadata"]["governance"]


def test_con_servidores_el_gobierno_lleva_una_entrada_por_servidor() -> None:
    manifest = _manifest(mcp_server_1="jira", mcp_server_2="confluence",
                         mcp_accountable_team="platform-atlassian")
    assert set(manifest["metadata"]["governance"]["mcp"]) == {"jira", "confluence"}


def test_el_contrato_de_herramientas_no_se_siembra() -> None:
    # Lo escribe entero la máquina tras consultar `tools/list`. Un valor que nadie puso no puede
    # colarse en la solicitud de cambio como si alguien hubiera mirado el servidor.
    manifest = _manifest(mcp_server_1="jira", mcp_accountable_team="platform-atlassian")
    assert "tools_contract" not in manifest["metadata"]["governance"]["mcp"]["jira"]


def test_componer_el_manifiesto_no_modifica_la_plantilla_recibida() -> None:
    # La plantilla se lee una vez y podría reutilizarse para varias unidades.
    before = dict(TEMPLATE)
    _manifest(mcp_server_1="jira", mcp_accountable_team="platform-atlassian")
    assert TEMPLATE == before


def test_la_url_del_repositorio_se_arma_con_organizacion_y_nombre() -> None:
    assert _manifest()["repository"] == (
        "https://github.com/Banca-Agente-IA-demo/agents-modernization")


def test_la_conexion_del_servidor_queda_marcada_como_pendiente() -> None:
    # El formulario no pregunta por la URL ni por las credenciales: no son identidad, y un
    # formulario no es sitio para acercarse a un secreto.
    config = build_mcp_config(("jira",))
    assert config["mcpServers"]["jira"]["command"].startswith("PENDIENTE")
