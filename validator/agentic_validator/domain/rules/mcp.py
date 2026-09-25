"""El único servidor MCP de la unidad: una unidad, un servidor (D2), y sus credenciales por nombre.

La conexión vive en `.mcp.json` y el gobierno en el bloque `mcp`; ninguno repite lo del otro. Lo que
se comprueba aquí es que digan lo mismo y que ninguna credencial viaje como valor literal (C2).
"""

from __future__ import annotations

import re

from agentic_validator.domain.findings import Finding, error
from agentic_validator.domain.snapshot import UnitSnapshot
from agentic_validator.domain.standard import (
    CLIENT_VARIABLES,
    GOVERNANCE_FILE,
    MCP_FILE,
    MIN_SECRET_VALUE_LENGTH,
    SECRET_LIKE_CONNECTION_KEYS,
)

# Formas con las que los clientes referencian una variable, medidas en la demo anterior. Se miran
# `env` y `headers`; en `args` una ${VAR} es casi siempre una ruta.
_VARIABLE = re.compile(r"\$\{(?:(?:input|env|secrets|localEnv):)?([A-Za-z_][A-Za-z0-9_]*)\}")
_CREDENTIAL_HOLDERS = ("env", "headers")


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


def check_every_server_has_an_accountable_team(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Todo servidor declara un equipo del banco que responde por él, tenga credenciales o no.

    Responde, no posee: el servidor es de quien lo opera, y ningún equipo del banco es dueño del MCP
    de Atlassian. Lo que se declara es quién avala internamente que esté aquí.

    Antes sólo se exigía cuando la conexión usaba algún `${VAR}`, y eso dejaba entrar sin aval a los
    servidores externos **sin autenticación**: pedir una credencial era, en la práctica, la única
    conversación que obligaba a que alguien mirara ese servidor, y un endpoint público se pegaba en el
    `.mcp.json` sin hablar con nadie. Sin autenticación no hay menos riesgo, hay otro riesgo: lo que
    importa en un banco no es quién guarda la llave, es qué sale por ahí.

    Con credenciales, el dueño es además quien las concede. Sin ellas, es quien avala que ese endpoint
    puede recibir datos del banco.
    """
    servers = _servers(snapshot)
    if not servers:
        return ()
    block = (snapshot.governance or {}).get("mcp")
    if not isinstance(block, dict):
        block = {}
    findings: list[Finding] = []
    for server in sorted(str(name) for name in servers):
        governance = block.get(server)
        accountable = governance.get("accountable_team") if isinstance(governance, dict) else None
        if accountable:
            continue
        pide_credenciales = bool(observed_credentials(snapshot).get(server))
        porque = (
            "quien la instale no sabrá a quién pedir el acceso"
            if pide_credenciales
            else "nadie avala que ese servidor pueda recibir datos del banco"
        )
        findings.append(
            error(
                "mcp.server-without-accountable-team",
                GOVERNANCE_FILE,
                f"el gobierno de {server} no declara accountable_team: {porque}",
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
    if len(value) < MIN_SECRET_VALUE_LENGTH:
        return False
    return any(marker in key.lower() for marker in SECRET_LIKE_CONNECTION_KEYS)
