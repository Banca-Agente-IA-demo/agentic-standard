"""Permisos mínimos (C1): lo declarado contra lo que hay en el árbol."""

from __future__ import annotations

from agentic_validator.domain.rules import permissions

from tests.validator.units import hooks_config, snapshot, text_artifact, with_governance


def _rules(snap) -> list[str]:
    findings = (
        permissions.check_declared_permissions_are_lists(snap)
        + permissions.check_agent_tools(snap)
        + permissions.check_hook_commands(snap)
    )
    return [f.rule for f in findings]


def test_un_agente_que_usa_una_herramienta_declarada_no_produce_hallazgo():
    snap = snapshot(
        governance=with_governance(permissions={"tools": ["Read"], "commands": [], "mcp_servers": []}),
        agents=(text_artifact("agents/a.agent.md", "a", name="a", tools=["Read"]),),
    )
    assert _rules(snap) == []


def test_un_agente_que_usa_una_herramienta_no_declarada_es_error():
    snap = snapshot(agents=(text_artifact("agents/a.agent.md", "a", name="a", tools=["Bash"]),))
    assert "permissions.tool-undeclared" in _rules(snap)


def test_los_patrones_de_herramienta_mcp_no_se_cuentan_como_herramientas_del_cliente():
    # Se gobiernan por mcp_servers y sus reglas propias, no por permissions.tools.
    tools = ["mcp__plugin_demo-unit_jira__*", "jira/*"]
    snap = snapshot(agents=(text_artifact("agents/a.agent.md", "a", name="a", tools=tools),))
    assert "permissions.tool-undeclared" not in _rules(snap)


def test_un_hook_que_invoca_un_ejecutable_no_declarado_es_error():
    snap = snapshot(hooks=hooks_config())
    assert "permissions.command-undeclared" in _rules(snap)


def test_un_hook_cuyo_ejecutable_esta_declarado_no_produce_hallazgo():
    snap = snapshot(
        governance=with_governance(permissions={"tools": [], "commands": ["check.sh"], "mcp_servers": []}),
        hooks=hooks_config(),
    )
    assert "permissions.command-undeclared" not in _rules(snap)


def test_un_ejecutable_del_sistema_se_reconoce_por_su_nombre_sin_ruta():
    snap = snapshot(
        governance=with_governance(permissions={"tools": [], "commands": ["mvn"], "mcp_servers": []}),
        hooks=hooks_config(command="mvn -q verify"),
    )
    assert "permissions.command-undeclared" not in _rules(snap)


def test_una_lista_de_permisos_que_falta_es_error():
    # Las tres son obligatorias aunque estén vacías: una vacía afirma que no se usa nada de ese tipo.
    snap = snapshot(governance=with_governance(permissions={"tools": []}))
    assert "permissions.list-missing" in _rules(snap)
