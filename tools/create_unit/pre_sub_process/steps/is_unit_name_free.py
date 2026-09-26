"""Paso 4 de create-unit · determinista · puro.

Decir si el nombre de la unidad está libre en el catálogo que se acaba de leer.

EL NOMBRE DE LA UNIDAD ES EL IDENTIFICADOR DE SU FICHA. Medido el 24 de septiembre de 2026: la
entidad de `agentic_unit` se identifica como `spring-to-quarkus`, que es su `name`. Por eso la
comparación es contra los identificadores y no contra los títulos.

NO PREGUNTA NADA Y NO ESCRIBE. Recibe la lista ya leída, así que se prueba sin red y sin dobles: es
el sitio donde la decisión se puede mirar a ojo.

NO CIERRA LA VENTANA DE COLISIÓN, solo la estrecha. La ficha nace al final del flujo, así que dos
autores simultáneos pueden pasar los dos por aquí. Lo que la cierra es el 409 del registro.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 5. AGENTS.md S5, S6 y PR6.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from create_unit.commons.models.catalog_units import CatalogUnits
    from create_unit.commons.models.seams import PayloadReading

__all__ = ["is_unit_name_free"]

log = logging.getLogger(__name__)


def is_unit_name_free(reading: PayloadReading, catalog: CatalogUnits) -> bool:
    """Si nadie ocupa todavía ese nombre.

    Devuelve `False` cuando no hay petición, y no es una respuesta inventada: sin nombre no hay nada
    que reservar, y el paso que compone la respuesta ya distingue ese caso por la petición ausente.
    """
    if reading.request is None:
        return False
    free = reading.request.name not in catalog.names
    log.debug("nombre %s libre=%s", reading.request.name, free)
    return free
