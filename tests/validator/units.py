"""Construcción de unidades e instantáneas para las pruebas del validador.

Dos formas complementarias: `build_unit` escribe una unidad real en disco a partir de las plantillas
del repositorio, que es como se comprueba de punta a punta (SC-002); `snapshot` construye una
instantánea en memoria, que es como se prueban las reglas sin tocar disco (T1).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from agentic_validator.domain.model import TextArtifact, UnitSnapshot

from tests.templates.markers import instantiate, read_template

REPO_ROOT = Path(__file__).resolve().parents[2]

UNIT_NAME = "demo-unit"
REPOSITORY = "agents-demo"
SERVER = "jira"
CREDENTIAL = "JIRA_TOKEN"


def build_unit(base: Path, *, with_mcp: bool = False, with_hooks: bool = False) -> Path:
    """Escribe una unidad instanciada de las plantillas en `<base>/<repositorio>/plugins/<unidad>`."""
    root = base / REPOSITORY / "plugins" / UNIT_NAME
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        instantiate(read_template("plugin-unit/.claude-plugin/plugin.json")), encoding="utf-8"
    )
    governance = json.loads(instantiate(read_template("plugin-unit/GOVERNANCE.json")))
    if with_mcp:
        block = json.loads(instantiate(read_template("artifacts/mcp/mcp-governance-block.json")))
        governance["permissions"] = {**governance["permissions"], "mcp_servers": [SERVER]}
        governance["mcp"] = block["mcp"]
        (root / ".mcp.json").write_text(instantiate(read_template("artifacts/mcp/.mcp.json")), encoding="utf-8")
    if with_hooks:
        governance["permissions"] = {**governance["permissions"], "commands": ["check.sh"]}
        (root / "hooks").mkdir()
        hooks = json.loads(read_template("artifacts/hooks/hooks.json"))
        action = hooks["hooks"]["PostToolUse"][0]["hooks"][0]
        action["command"] = "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check.sh"
        hooks["hooks"]["PostToolUse"][0]["matcher"] = "Edit"
        (root / "hooks" / "hooks.json").write_text(json.dumps(hooks, indent=2), encoding="utf-8")
    write_governance(root, governance)
    return root


def write_governance(root: Path, governance: dict) -> None:
    (root / "GOVERNANCE.json").write_text(json.dumps(governance, indent=2, ensure_ascii=False), encoding="utf-8")


def read_governance(root: Path) -> dict:
    return json.loads((root / "GOVERNANCE.json").read_text(encoding="utf-8"))


def add_skill(root: Path, name: str = "demo-skill") -> Path:
    """Añade un skill válido y devuelve la ruta de su archivo."""
    directory = root / "skills" / name
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: Revisa algo concreto. Úsalo cuando alguien lo pida.\n---\n\n# Título\n",
        encoding="utf-8",
    )
    return path


def add_agent(root: Path, name: str = "demo-agent", *, tools: list[str] | None = None) -> Path:
    directory = root / "agents"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.agent.md"
    declared = tools if tools is not None else ["Read"]
    lines = "\n".join(f"  - {tool!r}" for tool in declared)
    path.write_text(
        f"---\nname: {name}\ndescription: Hace algo concreto.\ntools:\n{lines}\n---\n\n# Título\n",
        encoding="utf-8",
    )
    return path


# --- Instantáneas en memoria para las pruebas de reglas -------------------------------------------

VALID_GOVERNANCE = {
    "schema_version": "1.0",
    "id": f"{REPOSITORY}/{UNIT_NAME}",
    "owner": {"team": "squad-demo", "contact": "squad-demo@bcp.com.pe"},
    "data_classification": "internal",
    "permissions": {"tools": [], "commands": [], "mcp_servers": []},
    "external_content": "No procesa contenido externo.",
}
VALID_MANIFEST = {
    "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    "name": UNIT_NAME,
    "version": "0.1.0-beta.1",
    "description": "Unidad de prueba.",
}


def snapshot(**overrides) -> UnitSnapshot:
    """Instantánea válida por defecto, con sustituciones puntuales."""
    base = UnitSnapshot(
        name=UNIT_NAME,
        repository=REPOSITORY,
        governance=json.loads(json.dumps(VALID_GOVERNANCE)),
        manifest=json.loads(json.dumps(VALID_MANIFEST)),
    )
    return replace(base, **overrides)


def with_governance(**changes) -> dict:
    """El gobierno válido con campos cambiados o, si el valor es `None`, quitados."""
    governance = json.loads(json.dumps(VALID_GOVERNANCE))
    for key, value in changes.items():
        if value is None:
            governance.pop(key, None)
        else:
            governance[key] = value
    return governance


def text_artifact(path: str, expected_name: str, **frontmatter) -> TextArtifact:
    return TextArtifact(path=path, expected_name=expected_name, frontmatter=dict(frontmatter))


MCP_CONNECTION = {
    "mcpServers": {
        SERVER: {"type": "http", "url": "https://jira.example/mcp", "headers": {"Authorization": f"Bearer ${{{CREDENTIAL}}}"}}
    }
}
MCP_GOVERNANCE_BLOCK = {
    SERVER: {
        "write_operations": False,
        "credentials": [CREDENTIAL],
        "credentials_owner": {"team": "plataforma-atlassian", "access_request_url": "https://example/accesos"},
        "tools_digest": "sha256:" + "0" * 64,
    }
}


def mcp_governance() -> dict:
    """El gobierno válido de una unidad que lleva su único servidor."""
    return with_governance(
        permissions={"tools": [], "commands": [], "mcp_servers": [SERVER]},
        mcp=json.loads(json.dumps(MCP_GOVERNANCE_BLOCK)),
    )


def unit_with_mcp(**overrides) -> UnitSnapshot:
    defaults = {"governance": mcp_governance(), "mcp": json.loads(json.dumps(MCP_CONNECTION))}
    return snapshot(**{**defaults, **overrides})


def hooks_config(*, event: str = "PostToolUse", command: str = "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/check.sh", **action_overrides) -> dict:
    action = {"type": "command", "command": command, "timeout": 5}
    action.update(action_overrides)
    return {"hooks": {event: [{"matcher": "Edit", "hooks": [action]}]}}
