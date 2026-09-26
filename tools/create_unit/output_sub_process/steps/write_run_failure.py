"""Paso 2 de la banda de salida · con efecto · devuelve el motivo a quien rellenó el formulario.

Por qué existe. Es la caja `handle error response` del diagrama de autoría, y está **dentro** del
paso de Python, no en el YAML. El motivo es que quien conoce el motivo es este proceso: sacarlo al
workflow obligaría a exportarlo como output, formatearlo en una expresión y volver a entrar por otra
action, con tres sitios donde el texto puede quedarse por el camino.

Qué cubre y qué no. Informa del veredicto que NO permite seguir. No informa del éxito: ese lo
comunica el registro en el catálogo, cuando la unidad ya existe de verdad y hay algo que anunciar.
Tampoco repara nada (C7).

POR QUÉ NO LANZA CUANDO PORT NO RESPONDE. El veredicto ya está decidido y el esqueleto, si procedía,
ya está compuesto. Convertir un fallo al avisar en un fallo de la creación cambiaría el desenlace por
culpa del canal de aviso. Se deja constancia en el log y se sigue.

Trazabilidad. `create_unit.drawio`, caja `handle error response`. AGENTS.md E4, P2, S6, C7.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from create_unit.commons.enums.validation_status import ValidationStatus
from port_catalog.action_run import RunStatus, report_run
from port_catalog.errors import CatalogError

if TYPE_CHECKING:  # pragma: no cover
    from create_unit.commons.models.seams import CreationOutcome
    from port_catalog.client import PortClient

__all__ = ["write_run_failure"]

log = logging.getLogger(__name__)


def write_run_failure(outcome: CreationOutcome, run_id: str, client: PortClient) -> None:
    """Escribe el motivo en la ejecución de Port. No hace nada cuando no hay motivo ni destinatario.

    `run_id` vacío es el caso de una invocación fuera del autoservicio: no hay ejecución a la que
    responder y no es un error.
    """
    if outcome.status is ValidationStatus.VALID or not run_id:
        return
    try:
        report_run(client, run_id, RunStatus.FAILURE, outcome.reason)
    except CatalogError as error:
        log.warning("no se pudo devolver el motivo a Port: %s", error)
