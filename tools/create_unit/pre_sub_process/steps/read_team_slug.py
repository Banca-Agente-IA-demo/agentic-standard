"""Paso 2 de create-unit · consulta al catálogo.

Traducir el equipo dueño a su slug, cuando el formulario lo envió como identificador numérico.

POR QUÉ HACE FALTA Y NO SOBRA CON LA FRONTERA. La frontera ya extrae el slug cuando Port manda la
entidad entera, que es lo medido el 25 de septiembre de 2026. Pero un disparo desde la API o una
versión anterior de la acción mandan el identificador desnudo, y entonces llega el id numérico de
GitHub. Un manifiesto que declarase `"author": {"name": "19716830"}` no serviría para avisar a
nadie, que es justo para lo que existe ese campo.

NO VALIDA NADA, NO ESCRIBE Y NO DECIDE SI SE SIGUE. Devuelve la misma lectura con el equipo
resuelto, o la misma lectura intacta cuando no hay petición que resolver.

NO SE HACE EN LA BANDA DE ENTRADA aunque lo parezca: es una pregunta a un servicio externo, y la
banda de entrada tiene que poder correr sin red.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 5. AGENTS.md S4, S5 y C8.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from create_unit.commons.models.seams import PayloadReading
from port_catalog.team_lookup import resolve_team_slug

if TYPE_CHECKING:  # pragma: no cover
    from port_catalog.client import PortClient

__all__ = ["read_team_slug"]

log = logging.getLogger(__name__)


def read_team_slug(reading: PayloadReading, client: PortClient) -> PayloadReading:
    """La misma lectura con el equipo dueño ya en forma de slug.

    Cuando no hay petición no pregunta nada: un formulario mal formado no debe gastar una llamada al
    catálogo ni un token.
    """
    if reading.request is None:
        return reading
    slug = resolve_team_slug(client, reading.request.owner_team)
    log.debug("equipo dueno resuelto a %s", slug)
    return PayloadReading(request=reading.request.model_copy(update={"owner_team": slug}),
                          detail=reading.detail)
