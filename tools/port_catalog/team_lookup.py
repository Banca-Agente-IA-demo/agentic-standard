"""Traduce el identificador de un equipo de GitHub a su slug.

POR QUÉ HACE FALTA. El formulario ofrece los equipos de GitHub, que Port sincroniza en el blueprint
`githubTeam`. Pero esas entidades **se identifican por el id numérico de GitHub**, no por el slug:

    identifier: 19716830     title: squad-cnf-migration     properties.slug: squad-cnf-migration

Así que el payload llega con `owner_team = "19716830"`. Un manifiesto que declarase
`"author": {"name": "19716830"}` no serviría para nada: ese campo existe para que una persona sepa a
quién avisar cuando la unidad se suspenda.

POR QUÉ SE OFRECEN LOS DE GITHUB Y NO LOS DE PORT. El blueprint `_team` es el modelo de identidad de
Port y se alimenta del IdP; `githubTeam` es el espejo de los equipos reales. El esquema de gobierno
dice del equipo dueño que es el «slug del equipo, que debe existir en la organización de GitHub», y
si el control lo va a resolver contra GitHub, el formulario tiene que ofrecer los de GitHub.

Medido el 25 de septiembre de 2026: los diez equipos de la organización aparecen en `githubTeam`
segundos después de crearlos.
"""

from __future__ import annotations

import logging

from port_catalog.client import PortClient
from port_catalog.errors import CatalogUnavailableError

__all__ = ["TEAM_BLUEPRINT", "resolve_team_slug"]

log = logging.getLogger(__name__)

# El blueprint del espejo de los equipos de GitHub, que trae el exportador de Port.
TEAM_BLUEPRINT = "githubTeam"


def resolve_team_slug(client: PortClient, owner_team: str) -> str:
    """El slug del equipo, venga como id numérico o ya como slug.

    Acepta las dos formas a propósito: el formulario envía el id, pero un disparo desde la API o una
    versión anterior de la acción envían el slug, y ninguno de los dos debe romperse.
    """
    if not owner_team.isdigit():
        return owner_team
    try:
        entity = client.get("/blueprints/%s/entities/%s" % (TEAM_BLUEPRINT, owner_team))["entity"]
    except (CatalogUnavailableError, KeyError):
        log.warning("no se pudo traducir el equipo %s a su slug; se usa tal cual", owner_team)
        return owner_team
    slug = entity.get("properties", {}).get("slug") or entity.get("title") or owner_team
    log.debug("equipo %s resuelto a %s", owner_team, slug)
    return slug
