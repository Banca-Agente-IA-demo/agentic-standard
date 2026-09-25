"""Crea la ficha de una unidad en el catálogo, y falla si el nombre ya está tomado.

POR QUÉ CREAR Y NO ACTUALIZAR. La operación de actualización de Port es una reescritura silenciosa:
usarla aquí convertiría un choque de nombres en el **borrado de la ficha ajena**, sin un solo error.
Medido el 25 de septiembre de 2026: un `POST` sin `upsert` sobre un identificador existente devuelve
409 `identifier_taken`, que es exactamente el comportamiento que el diseño pide.

POR QUÉ LA FICHA NACE AL FINAL. Se crea cuando la siembra ya salió bien, así que entre el envío del
formulario y el registro hay una ventana en la que dos autores pueden ir con el mismo nombre. Este
409 es lo único que la cierra: la comprobación previa contra el catálogo reduce el choque, no lo
elimina.

EL ESTADO NO SE TECLEA. Una unidad con ficha y sin ningún release está en Desarrollo, y eso es lo que
la ficha declara al nacer. Ninguna otra transición pasa por aquí.

Trazabilidad. Documento 04 §2 del entregable E2, apartado 5.bis de `DISENO-CREACION-DESDE-PORT.md` y
el blueprint `agentic_unit`.
"""

from __future__ import annotations

import logging

from port_catalog.client import PortClient
from port_catalog.errors import CatalogUnavailableError, UnitAlreadyRegisteredError
from port_catalog.unit_lookup import UNIT_BLUEPRINT

__all__ = ["INITIAL_STATE", "register_unit", "unregister_unit"]

log = logging.getLogger(__name__)

# El estado con el que nace toda unidad: hay ficha y ningún release. No se deriva de nada más porque
# en este punto todavía no hay nada de lo que derivarlo.
INITIAL_STATE = "desarrollo"

_IDENTIFIER_TAKEN = "identifier_taken"


def register_unit(client: PortClient, *, name: str, form: str, owner_team: str,
                  owner_contact: str, risk_level: str, repository: str, path: str,
                  sha: str, mcp_servers: tuple[str, ...]) -> None:
    """Escribe la ficha. Es el único efecto de este módulo sobre el catálogo.

    Los argumentos van por nombre y sin valor por defecto: son nueve campos del mismo tipo y por
    posición cualquier trasposición pasaría desapercibida.
    """
    body = {
        "identifier": name,
        "title": name,
        "properties": {
            "state": INITIAL_STATE,
            "form": form,
            "owner_team": owner_team,
            "owner_contact": owner_contact,
            "risk_level": risk_level,
            "repo": repository,
            "path": path,
            "sha": sha,
            "mcp_servers": list(mcp_servers),
        },
    }
    try:
        client.post("/blueprints/%s/entities" % UNIT_BLUEPRINT, body)
    except CatalogUnavailableError as exc:
        if _IDENTIFIER_TAKEN in str(exc):
            raise UnitAlreadyRegisteredError(
                "El nombre %s ya esta ocupado por otra unidad del catalogo. "
                "Elige otro y vuelve a enviar el formulario." % name) from exc
        raise
    log.info("ficha de %s creada en estado %s", name, INITIAL_STATE)


def unregister_unit(client: PortClient, name: str) -> None:
    """Retira la ficha recién creada cuando el resto de la creación no se pudo completar.

    Existe para que no quede una unidad en Desarrollo sin código, indistinguible de una abandonada:
    o existen la ficha y la rama, o no existe ninguna de las dos.
    """
    try:
        client.delete("/blueprints/%s/entities/%s" % (UNIT_BLUEPRINT, name))
    except CatalogUnavailableError as exc:
        # Que la compensación falle no puede tapar el fallo que la provocó, así que se avisa y se
        # sigue: quien lea el registro necesita ver los dos.
        log.warning("no se pudo retirar la ficha de %s: %s", name, exc)
        return
    log.info("ficha de %s retirada", name)
