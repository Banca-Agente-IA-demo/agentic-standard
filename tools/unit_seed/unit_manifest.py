"""Compone el manifiesto de la unidad a partir de la plantilla y de la petición del formulario.

Por qué existe. La forma del manifiesto vive ENTERA en `templates/unit/plugin.json`, incluido
`metadata.governance`. Este módulo solo sustituye marcadores y añade el único bloque que no cabe en
una plantilla estática. Describir aquí la forma otra vez daría dos sitios que definen lo mismo y que
divergen sin que nadie lo note (C4), que es exactamente lo que pasaba cuando la plantilla emitía un
`GOVERNANCE.json` y el gobierno se construía en Python.

Qué cubre y qué no. No lee la plantilla del disco: la recibe ya parseada, así que se prueba sin
`tmp_path`. No decide rutas, que son de `unit_layout`.

Trazabilidad. Documento 02 §1 y §2 del entregable E2. AGENTS.md C3, C4 y P4.
"""

from __future__ import annotations

import json

from unit_seed.unit_request import UnitRequest

__all__ = ["build_manifest", "build_mcp_config", "INITIAL_VERSION", "UNFINISHED_MARK"]

# La versión de toda unidad recién creada. Nace con sufijo de prelanzamiento para que su primer
# release lleve `prerelease` y entre al canal experimental en vez de a producción.
INITIAL_VERSION = "0.1.0-beta.1"

# El texto que hace visible que algo está sin terminar. Tiene que ser reconocible: una descripción
# plausible convierte «sin completar» en indetectable, y el esqueleto debe fallar el gate de forma
# evidente, no parecer una unidad terminada.
UNFINISHED_MARK = "PENDIENTE: describir qué hace y cuándo debe activarse"


def build_manifest(request: UnitRequest, template: dict) -> dict:
    """La plantilla con sus marcadores sustituidos, más el bloque `mcp` cuando hay servidores.

    No muta `template`: la sustitución se hace sobre su serialización y devuelve un objeto nuevo (P4).
    """
    organization, repository = _split_repository(request.repository)
    manifest = json.loads(
        json.dumps(template)
        .replace("<<NAME>>", request.name)
        .replace("<<VERSION>>", INITIAL_VERSION)
        .replace("<<DESCRIPTION>>", request.description)
        .replace("<<TEAM>>", request.owner_team)
        .replace("<<TEAM_MAILBOX>>", request.team_mailbox)
        .replace("<<ORG>>", organization)
        .replace("<<REPO>>", repository)
        .replace("<<RISK_LEVEL>>", request.risk_level.value)
    )
    if not request.mcp_servers:
        return manifest
    # El bloque no cabe en una plantilla estática: su número de entradas depende de cuántos
    # servidores declaró el formulario. `tools_contract` NO se siembra: lo observa la máquina
    # consultando el servidor, y aquí no hay servidor todavía.
    governance = manifest["metadata"]["governance"]
    return {
        **manifest,
        "metadata": {
            **manifest["metadata"],
            "governance": {
                **governance,
                "mcp": {server: {"accountable_team": request.mcp_accountable_team}
                        for server in request.mcp_servers},
            },
        },
    }


def build_mcp_config(servers: tuple[str, ...]) -> dict:
    """Un solo archivo con una clave por servidor. La conexión la completa el asistente de autoría.

    El formulario no pregunta por la URL, el comando ni las variables de credencial: no son identidad,
    y un formulario no es sitio para acercarse a un secreto.
    """
    return {"mcpServers": {server: {"command": UNFINISHED_MARK, "args": []}
                           for server in servers}}


def _split_repository(repository: str) -> tuple[str, str]:
    """Separa `organizacion/repositorio`. Devuelve siempre dos cadenas, nunca una lista variable."""
    organization, _, name = repository.partition("/")
    return organization, name
