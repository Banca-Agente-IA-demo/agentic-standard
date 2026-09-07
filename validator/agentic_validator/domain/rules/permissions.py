"""Permisos mínimos (C1): lo declarado se contrasta con lo que hay en el árbol.

Una declaración que nadie contrasta es documentación, no gobierno. Sólo se compara contra lo
estructurado: las herramientas de cada agente, los ejecutables de cada hook y el servidor de la
configuración. Sobre skills y prompts no hay nada comparable y la revisión es humana.
"""

from __future__ import annotations

from agentic_validator.domain.model import GOVERNANCE_FILE, HOOKS_FILE, Finding, UnitSnapshot, error
from agentic_validator.domain.rules.hooks import command_actions

# Un patrón de herramienta MCP no es una herramienta del cliente: se gobierna por mcp_servers y sus
# reglas propias, no por permissions.tools.
_MCP_TOOL_MARKERS = ("mcp__", "/*")


def _is_mcp_tool_pattern(tool: str) -> bool:
    return tool.startswith("mcp__") or tool.endswith("/*")


def check_agent_tools(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Toda herramienta de cliente que un agente declara está en los permisos de la unidad."""
    declared = set(snapshot.permissions("tools"))
    findings: list[Finding] = []
    for agent in snapshot.agents:
        tools = (agent.frontmatter or {}).get("tools")
        if not isinstance(tools, list):
            continue
        for tool in tools:
            name = str(tool)
            if _is_mcp_tool_pattern(name) or name in declared:
                continue
            findings.append(
                error(
                    "permissions.tool-undeclared",
                    agent.path,
                    f"el agente usa la herramienta {name!r} y permissions.tools no la declara",
                )
            )
    return tuple(findings)


def check_hook_commands(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Todo ejecutable que un hook invoca está en los permisos de la unidad."""
    declared = set(snapshot.permissions("commands"))
    findings: list[Finding] = []
    for event, action in command_actions(snapshot):
        executable = _executable_of(str(action.get("command", "")))
        if not executable or executable in declared:
            continue
        findings.append(
            error(
                "permissions.command-undeclared",
                HOOKS_FILE,
                f"el hook de {event} invoca {executable!r} y permissions.commands no lo declara",
            )
        )
    return tuple(findings)


def _executable_of(command: str) -> str:
    """El nombre del ejecutable, sin ruta ni argumentos.

    Un comando de la unidad viaja como `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/x.sh`, así que el
    ejecutable es el último segmento; uno del sistema viaja como `mvn -q verify`.
    """
    first = command.strip().split()[0] if command.strip() else ""
    return first.rsplit("/", 1)[-1] if first else ""


def check_declared_permissions_are_lists(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Las tres listas son obligatorias aunque estén vacías: una vacía afirma que no se usa nada."""
    governance = snapshot.governance
    if governance is None:
        return ()
    declared = governance.get("permissions")
    if not isinstance(declared, dict):
        return ()  # la forma la impone el contrato
    missing = [key for key in ("tools", "commands", "mcp_servers") if not isinstance(declared.get(key), list)]
    if missing:
        return (
            error(
                "permissions.list-missing",
                GOVERNANCE_FILE,
                f"permissions no declara como lista: {', '.join(missing)}",
            ),
        )
    return ()
