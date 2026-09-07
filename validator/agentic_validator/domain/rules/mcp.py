"""El único servidor MCP de la unidad: una unidad, un servidor (D2), y sus credenciales por nombre.

La conexión vive en `.mcp.json` y el gobierno en el bloque `mcp`; ninguno repite lo del otro. Lo que
se comprueba aquí es que digan lo mismo y que ninguna credencial viaje como valor literal (C2).
"""

from __future__ import annotations

import re

from agentic_validator.domain.model import (
    CLIENT_VARIABLES,
    GOVERNANCE_FILE,
    MCP_FILE,
    Finding,
    UnitSnapshot,
    error,
)

# Formas con las que los clientes referencian una variable, medidas en la demo anterior. Se miran
# `env` y `headers`; en `args` una ${VAR} es casi siempre una ruta.
_VARIABLE = re.compile(r"\$\{(?:(?:input|env|secrets|localEnv):)?([A-Za-z_][A-Za-z0-9_]*)\}")
_CREDENTIAL_HOLDERS = ("env", "headers")

# Un valor con pinta de secreto en claro: cadena larga sin ${...} en una clave que suele llevarlo.
_SECRET_LIKE_KEYS = ("authorization", "token", "secret", "password", "api_key", "apikey", "key")
_MIN_SECRET_LENGTH = 12


def _servers(snapshot: UnitSnapshot) -> dict:
    servers = (snapshot.mcp or {}).get("mcpServers")
    return servers if isinstance(servers, dict) else {}


def check_mcp_readable(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    if snapshot.mcp_error:
        return (error("mcp.unreadable", MCP_FILE, f"no se pudo interpretar: {snapshot.mcp_error}"),)
    if snapshot.mcp is not None and not _servers(snapshot):
        return (error("mcp.no-servers", MCP_FILE, "el archivo no declara ningún servidor en mcpServers"),)
    return ()


def check_single_server(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """D2: la aprobación de Ciberseguridad y Riesgo operacional es de un contrato, no de varios."""
    servers = _servers(snapshot)
    if len(servers) > 1:
        return (
            error(
                "mcp.more-than-one-server",
                MCP_FILE,
                f"la unidad declara {len(servers)} servidores ({', '.join(sorted(servers))}) y sólo puede llevar uno",
            ),
        )
    return ()


def check_governance_block_matches(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El bloque de gobierno existe si y sólo si hay configuración, y con la misma clave."""
    governance = snapshot.governance
    if governance is None:
        return ()
    block = governance.get("mcp")
    servers = _servers(snapshot)
    findings: list[Finding] = []
    if servers and not isinstance(block, dict):
        findings.append(
            error("mcp.governance-block-missing", GOVERNANCE_FILE, "la unidad lleva servidor y el gobierno no lo declara")
        )
        return tuple(findings)
    if isinstance(block, dict) and not snapshot.has_mcp:
        findings.append(
            error("mcp.governance-block-orphan", GOVERNANCE_FILE, "el gobierno declara un servidor y la unidad no lo configura")
        )
        return tuple(findings)
    if not servers or not isinstance(block, dict):
        return ()
    configured = set(servers)
    governed = set(block)
    if configured != governed:
        findings.append(
            error(
                "mcp.server-name-mismatch",
                GOVERNANCE_FILE,
                f"la configuración declara {sorted(configured)} y el gobierno {sorted(governed)}; deben ser la misma clave",
            )
        )
    permitted = set(snapshot.permissions("mcp_servers"))
    if configured != permitted:
        findings.append(
            error(
                "mcp.server-not-in-permissions",
                GOVERNANCE_FILE,
                f"permissions.mcp_servers declara {sorted(permitted)} y la configuración {sorted(configured)}",
            )
        )
    return tuple(findings)


def observed_credentials(snapshot: UnitSnapshot) -> dict[str, set[str]]:
    """Nombres de variable referenciados por cada servidor en `env` y `headers`."""
    found: dict[str, set[str]] = {}
    for name, definition in _servers(snapshot).items():
        if not isinstance(definition, dict):
            continue
        names: set[str] = set()
        for holder in _CREDENTIAL_HOLDERS:
            values = definition.get(holder)
            if not isinstance(values, dict):
                continue
            for value in values.values():
                names.update(v for v in _VARIABLE.findall(str(value)) if v not in CLIENT_VARIABLES)
        found[str(name)] = names
    return found


def check_credentials_match(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Cotejo en los dos sentidos: usar sin declarar es error, y declarar sin usar también."""
    block = (snapshot.governance or {}).get("mcp")
    if not isinstance(block, dict):
        return ()
    observed = observed_credentials(snapshot)
    findings: list[Finding] = []
    for server, governance in block.items():
        if not isinstance(governance, dict):
            continue
        declared = set(governance.get("credentials") or [])
        used = observed.get(str(server), set())
        for name in sorted(used - declared):
            findings.append(
                error(
                    "mcp.credential-undeclared",
                    MCP_FILE,
                    f"la conexión de {server} usa {name!r} y el gobierno no la declara en credentials",
                )
            )
        for name in sorted(declared - used):
            findings.append(
                error(
                    "mcp.credential-unused",
                    GOVERNANCE_FILE,
                    f"el gobierno de {server} declara {name!r} y la conexión no la usa",
                )
            )
    return tuple(findings)


def check_no_literal_secrets(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C2: la unidad viaja sin el secreto; en la conexión sólo aparece el nombre de la variable."""
    findings: list[Finding] = []
    for name, definition in _servers(snapshot).items():
        if not isinstance(definition, dict):
            continue
        for holder in _CREDENTIAL_HOLDERS:
            values = definition.get(holder)
            if not isinstance(values, dict):
                continue
            for key, value in values.items():
                if _looks_like_a_literal_secret(str(key), str(value)):
                    findings.append(
                        error(
                            "mcp.literal-secret",
                            MCP_FILE,
                            f"{holder}.{key} de {name} lleva un valor literal donde debería ir ${{VARIABLE}}",
                        )
                    )
    return tuple(findings)


def _looks_like_a_literal_secret(key: str, value: str) -> bool:
    if "${" in value:
        return False
    if len(value) < _MIN_SECRET_LENGTH:
        return False
    return any(marker in key.lower() for marker in _SECRET_LIKE_KEYS)
