"""Se hace cargo de que un agente restrinja el servidor de su unidad en las dos grafías (D7).

Es la única regla del estándar que existe porque los dos clientes escriben lo mismo de forma distinta.
Vive aparte del resto de reglas de artefactos porque su razón de ser no es el formato del artefacto,
sino la portabilidad medida entre clientes: el día que las grafías converjan, este módulo desaparece
entero.
"""

from __future__ import annotations

from agentic_validator.domain.findings import Finding, error, warning
from agentic_validator.domain.snapshot import UnitSnapshot

# Las dos grafías con las que un agente restringe su servidor. Medido el 7 de septiembre de 2026 (D7):
# cada cliente ignora en silencio la que no entiende, así que hacen falta las dos.
CLAUDE_MCP_TOOL_PREFIX = "mcp__plugin_"
COPILOT_MCP_TOOL_SUFFIX = "/*"


def check_agent_mcp_spellings(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """D7: si el agente restringe su servidor, declara las dos grafías; si no restringe, avisa."""
    if not snapshot.has_mcp:
        return ()
    findings: list[Finding] = []
    for agent in snapshot.agents:
        tools = (agent.frontmatter or {}).get("tools")
        if not isinstance(tools, list):
            findings.append(
                warning(
                    "artifact.agent-inherits-everything",
                    agent.path,
                    "el agente no declara tools y hereda todo lo instalado en la sesión, que es lo contrario de C1",
                )
            )
            continue
        names = [str(tool) for tool in tools]
        has_claude = any(name.startswith(CLAUDE_MCP_TOOL_PREFIX) for name in names)
        has_copilot = any(name.endswith(COPILOT_MCP_TOOL_SUFFIX) and not name.startswith("mcp__") for name in names)
        if not has_claude and not has_copilot:
            continue
        own_unit_marker = f"{CLAUDE_MCP_TOOL_PREFIX}{snapshot.name}_"
        foreign = [n for n in names if n.startswith(CLAUDE_MCP_TOOL_PREFIX) and not n.startswith(own_unit_marker)]
        if foreign:
            findings.append(
                error(
                    "artifact.agent-mcp-of-another-unit",
                    agent.path,
                    f"{foreign[0]!r} apunta al servidor de otra unidad; el servidor viaja en la misma unidad que el agente",
                )
            )
        if not has_claude:
            findings.append(
                error(
                    "artifact.agent-missing-claude-spelling",
                    agent.path,
                    "el agente restringe el servidor sólo con la grafía de Copilot; Claude rehúsa lanzarlo",
                )
            )
        if not has_copilot:
            findings.append(
                error(
                    "artifact.agent-missing-copilot-spelling",
                    agent.path,
                    "el agente restringe el servidor sólo con la grafía de Claude; Copilot lo arranca sin el servidor y no avisa",
                )
            )
    return tuple(findings)
