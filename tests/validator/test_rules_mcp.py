"""Una unidad, un servidor (D2), y las credenciales por nombre y nunca por valor (C2)."""

from __future__ import annotations

import copy

from agentic_validator.domain.rules import mcp

from tests.validator.units import CREDENTIAL, SERVER, snapshot, unit_with_mcp, with_governance


def _rules(snap) -> list[str]:
    findings = (
        mcp.check_mcp_readable(snap)
        + mcp.check_single_server(snap)
        + mcp.check_governance_block_matches(snap)
        + mcp.check_credentials_match(snap)
        + mcp.check_no_literal_secrets(snap)
    )
    return [f.rule for f in findings]


def test_una_unidad_con_su_unico_servidor_bien_declarado_no_produce_hallazgos():
    assert _rules(unit_with_mcp()) == []


def test_una_unidad_sin_servidor_no_produce_hallazgos():
    assert _rules(snapshot()) == []


def test_dos_servidores_en_la_configuracion_es_error():
    # D2: la aprobación de Ciberseguridad y Riesgo operacional es de un contrato, no de dos.
    snap = unit_with_mcp()
    connection = copy.deepcopy(snap.mcp)
    connection["mcpServers"]["confluence"] = copy.deepcopy(connection["mcpServers"][SERVER])
    assert "mcp.more-than-one-server" in _rules(snapshot(governance=snap.governance, mcp=connection))


def test_una_configuracion_sin_su_bloque_de_gobierno_es_error():
    snap = unit_with_mcp()
    assert "mcp.governance-block-missing" in _rules(snapshot(mcp=snap.mcp))


def test_un_bloque_de_gobierno_sin_configuracion_es_error():
    snap = unit_with_mcp()
    assert "mcp.governance-block-orphan" in _rules(snapshot(governance=snap.governance))


def test_la_clave_del_servidor_distinta_entre_configuracion_y_gobierno_es_error():
    snap = unit_with_mcp()
    connection = copy.deepcopy(snap.mcp)
    connection["mcpServers"]["otro"] = connection["mcpServers"].pop(SERVER)
    assert "mcp.server-name-mismatch" in _rules(snapshot(governance=snap.governance, mcp=connection))


def test_un_servidor_que_no_esta_en_los_permisos_es_error():
    snap = unit_with_mcp()
    governance = {**snap.governance, "permissions": {"tools": [], "commands": [], "mcp_servers": []}}
    assert "mcp.server-not-in-permissions" in _rules(snapshot(governance=governance, mcp=snap.mcp))


def test_una_credencial_usada_y_no_declarada_es_error():
    snap = unit_with_mcp()
    governance = copy.deepcopy(snap.governance)
    governance["mcp"][SERVER]["credentials"] = []
    assert "mcp.credential-undeclared" in _rules(snapshot(governance=governance, mcp=snap.mcp))


def test_una_credencial_declarada_y_no_usada_es_error():
    # El cotejo va en los dos sentidos: declarar de más también miente sobre lo que la unidad necesita.
    snap = unit_with_mcp()
    governance = copy.deepcopy(snap.governance)
    governance["mcp"][SERVER]["credentials"] = [CREDENTIAL, "OTRO_TOKEN"]
    assert "mcp.credential-unused" in _rules(snapshot(governance=governance, mcp=snap.mcp))


def test_las_variables_del_cliente_no_cuentan_como_credenciales():
    # ${CLAUDE_PLUGIN_ROOT} lo expande el cliente; contarlo daría un falso positivo en cada unidad.
    snap = unit_with_mcp()
    connection = copy.deepcopy(snap.mcp)
    connection["mcpServers"][SERVER]["env"] = {"ROOT": "${CLAUDE_PLUGIN_ROOT}/bin"}
    assert _rules(snapshot(governance=snap.governance, mcp=connection)) == []


def test_una_credencial_en_claro_en_la_conexion_es_error():
    # C2: la unidad viaja sin el secreto; el cliente lo pide al instalar.
    snap = unit_with_mcp()
    connection = copy.deepcopy(snap.mcp)
    connection["mcpServers"][SERVER]["headers"]["Authorization"] = "Bearer ghp_0123456789abcdef0123"
    rules = _rules(snapshot(governance=snap.governance, mcp=connection))
    assert "mcp.literal-secret" in rules


def test_un_archivo_de_conexion_ilegible_se_informa_como_hallazgo():
    assert "mcp.unreadable" in _rules(snapshot(mcp_error="JSON inválido: línea 2"))


def test_una_conexion_sin_servidores_es_error():
    assert "mcp.no-servers" in _rules(snapshot(mcp={"mcpServers": {}}))
