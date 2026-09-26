"""Paso 3 de create-unit · consulta al catálogo.

Leer los nombres de unidad que ya existen en el catálogo, en todos los estados.

POR QUÉ SE PREGUNTA A PORT Y NO AL ÍNDICE DEL MARKETPLACE. El índice lista lo PUBLICADO. Una unidad
en Desarrollo tiene ficha y ningún release, así que no aparece en él: dos autores podrían elegir el
mismo nombre el mismo día y los dos pasarían la comprobación. Y hay dos marketplaces, producción y
experimental, de modo que mirar uno dejaría pasar la colisión con el otro. El catálogo es el único
sitio donde están las tres poblaciones a la vez.

POR QUÉ SE TRAE LA LISTA ENTERA Y NO SE PREGUNTA POR UNA ENTIDAD. La pregunta por identificador es
más barata y responde lo mismo para una unidad. Se trae la lista porque el diagrama de autoría lo
pide así y porque la colisión por nombre de ARTEFACTO, que sigue pendiente, necesitará recorrerla:
con la lista ya en memoria no habrá que volver a hablar con Port.

NO DECIDE SI EL NOMBRE ESTÁ LIBRE. Eso es el predicado del paso siguiente. Aquí solo se lee.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 4 y 8. AGENTS.md C2, C8, S5 y S6.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from create_unit.commons.models.catalog_units import CatalogUnits, CatalogUnitsAnswer
from create_unit.commons.models.seams import PayloadReading
from port_catalog.unit_lookup import UNIT_BLUEPRINT

if TYPE_CHECKING:  # pragma: no cover
    from port_catalog.client import PortClient

__all__ = ["read_catalog_units"]

log = logging.getLogger(__name__)

_ENTITIES_PATH = "/blueprints/%s/entities" % UNIT_BLUEPRINT


def read_catalog_units(reading: PayloadReading, client: PortClient) -> CatalogUnits:
    """Los nombres de unidad ocupados. Vacío cuando no hay petición que comprobar.

    Vacío y no `None`: quien lo recibe cuenta nombres, y un `None` le obligaría a ramificar antes de
    contar (P7).
    """
    if reading.request is None:
        return CatalogUnits(names=())
    # LA ÚNICA VENTANA DE C8: lo que contesta Port no tiene tipo propio hasta la línea siguiente.
    answer = client.get(_ENTITIES_PATH)
    catalog = CatalogUnitsAnswer.model_validate(answer)
    names = tuple(entity.identifier for entity in catalog.entities)
    log.debug("catalogo leido con %d unidades", len(names))
    return CatalogUnits(names=names)
