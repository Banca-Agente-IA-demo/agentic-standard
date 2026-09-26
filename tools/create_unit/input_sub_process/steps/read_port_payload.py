"""Paso 1 de create-unit · determinista · frontera exterior.

Leer el formulario que envió Port y convertirlo en la petición de dominio.

NO COMPRUEBA SI EL NOMBRE ESTÁ LIBRE, NO HABLA CON EL CATÁLOGO Y NO ESCRIBE NADA. Comprueba la
FORMA de lo que llegó y nada más: que el nombre tenga la forma permitida, que el riesgo sea uno de
los tres, que una unidad individual traiga su tipo. Si el nombre está tomado es una pregunta al
catálogo, y va en la banda siguiente.

NO REIMPLEMENTA EL MODELO. Usa el mismo `UnitRequest` que después usa el sembrador. Si este paso
validara por su cuenta habría dos definiciones de «payload válido», y el día que divergieran este
paso diría que está bien y el sembrador reventaría a mitad, dejando el esqueleto escrito a medias.

NO LANZA cuando el formulario viene mal, y es deliberado: eso es una respuesta, no una
imposibilidad (X2). Solo propaga `OSError` cuando no puede ni leer el archivo, que sí lo es.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md C2, C3, C8, S5 y X2.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from create_unit.commons.models.seams import PayloadReading
from unit_seed.errors import SeedError
from unit_seed.unit_request import UnitRequest

__all__ = ["read_port_payload"]

log = logging.getLogger(__name__)

# Tope del motivo que se le devuelve a la persona. El volcado de pydantic nombra el campo y el
# porqué, que es lo que hace falta; lo que sobra es el enlace a la documentación que añade al final.
MAX_REASON_CHARS = 500


def read_port_payload(payload_file: Path) -> PayloadReading:
    """La petición de dominio, o el motivo legible por el que el formulario no describe ninguna."""
    # LA ÚNICA VENTANA DE C8, y es esta línea: lo que devuelve `json.loads` no tiene tipo propio
    # hasta que `model_validate` lo convierte. De la línea siguiente en adelante viaja el modelo.
    payload = json.loads(payload_file.read_text(encoding="utf-8"))
    try:
        request = UnitRequest.model_validate(payload)
    except (ValidationError, SeedError) as error:
        log.info("el formulario no describe una unidad sembrable: %s", error)
        return PayloadReading(request=None, detail=_readable(error))
    log.debug("formulario leido para la unidad %s", request.name)
    return PayloadReading(request=request, detail="")


def _readable(error: Exception) -> str:
    """El motivo en una frase, sin saltos de línea, para que quepa en la pantalla de Port."""
    return " ".join(str(error).split())[:MAX_REASON_CHARS]
