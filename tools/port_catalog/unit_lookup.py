"""Pregunta al catálogo si el nombre de una unidad está libre.

POR QUÉ SE PREGUNTA A PORT Y NO AL ÍNDICE DEL MARKETPLACE. El índice lista lo PUBLICADO. Una unidad
en Desarrollo tiene ficha y ningún release, así que no aparece en él: dos autores podrían elegir el
mismo nombre el mismo día y los dos pasarían la comprobación. Y hay dos marketplaces, producción y
experimental, de modo que mirar uno dejaría pasar la colisión con el otro. El catálogo es el único
sitio donde están las tres poblaciones a la vez.

EL NOMBRE DE LA UNIDAD ES EL IDENTIFICADOR DE SU FICHA. Medido el 24 de septiembre de 2026: la única
entidad de `agentic_unit` se identifica como `spring-to-quarkus`, que es su `name`. Por eso basta
preguntar si esa entidad existe, sin recorrer el catálogo entero.

Trazabilidad. Documento 02 §1.1 del entregable E2 y el apartado 5 de `DISENO-CREACION-DESDE-PORT.md`.
"""

from __future__ import annotations

import logging

from port_catalog.client import PortClient

__all__ = ["UNIT_BLUEPRINT", "is_name_taken"]

log = logging.getLogger(__name__)

# El blueprint de la unidad publicable. Es una clave ya persistida en Port: renombrarla no es
# renombrar, es migrar.
UNIT_BLUEPRINT = "agentic_unit"


def is_name_taken(client: PortClient, name: str) -> bool:
    """Si ya hay una ficha de unidad con ese nombre, en cualquier estado.

    Incluye las que están en Desarrollo, que es justo lo que el índice del marketplace no puede ver.
    """
    taken = client.exists("/blueprints/%s/entities/%s" % (UNIT_BLUEPRINT, name))
    log.debug("nombre %s ocupado=%s", name, taken)
    return taken
