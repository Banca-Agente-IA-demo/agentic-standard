"""Escribe en la ejecución de la acción de Port el resultado y su motivo legible.

QUÉ ES UNA EJECUCIÓN Y QUÉ NO. Es el registro de «alguien pulsó el formulario y esto pasó», y existe
desde ese instante. NO es la ficha de la unidad: si la validación falla, la ficha no llega a
existir, y la ejecución sí. Es lo que identifica `port_run_id`.

DOS COSAS MEDIDAS el 24 de septiembre de 2026, las dos con consecuencia de diseño:

- El campo se llama `summary`. Enviar `statusText` devuelve 422 `invalid_request`, nombrando la
  propiedad sobrante. No es un sinónimo: es un campo que no existe.
- Una ejecución que ya terminó NO admite cambios: 422 `run_exhausted`. Por eso el motivo se escribe
  desde dentro del workflow y antes de que acabe; un job que informara después no podría.

Trazabilidad. Apartado 6 de `FLUJO-CREATE-UNIT.md`.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from port_catalog.client import PortClient
from port_catalog.errors import CatalogUnavailableError, RunExhaustedError

__all__ = ["RunStatus", "report_run", "MAX_SUMMARY_CHARS"]

log = logging.getLogger(__name__)

# Tope del texto que se envía. Port lo muestra en la pantalla del formulario, y un volcado de log
# entero ahí no se lee: lo que la persona necesita es la frase que le dice qué corregir.
MAX_SUMMARY_CHARS = 1_000

_RUN_EXHAUSTED = "run_exhausted"


class RunStatus(StrEnum):
    """Los dos desenlaces que Port reconoce. Se leen como texto porque viajan en el cuerpo JSON."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


def report_run(client: PortClient, run_id: str, status: RunStatus, summary: str) -> None:
    """Cierra la ejecución con su motivo. Es el único efecto de este módulo sobre Port."""
    try:
        client.patch("/actions/runs/" + run_id,
                     {"status": status.value, "summary": summary[:MAX_SUMMARY_CHARS]})
    except CatalogUnavailableError as exc:
        if _RUN_EXHAUSTED in str(exc):
            raise RunExhaustedError(
                "la ejecución %s ya había terminado; el motivo no se pudo escribir" % run_id) from exc
        raise
    log.info("ejecución %s cerrada como %s", run_id, status.value)
