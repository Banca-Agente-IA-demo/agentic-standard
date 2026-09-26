"""Paso 6 de create-unit · determinista · puro.

Componer el veredicto que sale del paso: el estado, su motivo legible y lo que hay que transportar.

AQUÍ SE DECIDE CUÁL DE LOS TRES ESTADOS ES, y es el único sitio donde se decide. Los pasos
anteriores dejan hechos (hay petición o no la hay, el nombre está libre o no); traducirlos a una
rama de enrutado es esto.

EL MOTIVO SE DERIVA DEL ESTADO, no se arrastra desde donde se detectó. El único texto que viene de
fuera es el detalle de pydantic, porque nombra el campo que la persona escribió mal y eso no se
puede reconstruir aquí.

NO ESCRIBE, NO PREGUNTA NADA Y NO REPARA. Nombra y enruta (C7): si el nombre está tomado, lo dice;
no propone otro ni lo cambia.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 4 y 7. AGENTS.md C4, C7, S5 y T1.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from create_unit.commons.enums.validation_status import ValidationStatus
from create_unit.commons.models.seams import CreationOutcome

if TYPE_CHECKING:  # pragma: no cover
    from create_unit.commons.models.seams import NameCheck, PayloadReading, SeededSkeleton

__all__ = ["compose_validation_status"]

log = logging.getLogger(__name__)

# El motivo de cada estado que para el flujo. `VALID` no aparece porque no tiene motivo que dar, y
# escribirle uno vacío invitaría a mostrarlo. Lleva un hueco para el nombre donde el nombre importa.
_REASON = {
    ValidationStatus.MALFORMED_PAYLOAD: "El formulario no describe una unidad que se pueda sembrar. %s",
    ValidationStatus.NAME_TAKEN: ("El nombre %s ya esta ocupado por otra unidad del catalogo, en "
                                  "cualquier estado, incluido Desarrollo. Elige otro."),
}


def compose_validation_status(reading: PayloadReading, check: NameCheck,
                              skeleton: SeededSkeleton) -> CreationOutcome:
    """El veredicto completo, con las mismas cinco claves valga lo que valga el estado."""
    status = _status_of(reading, check)
    request = check.request
    outcome = CreationOutcome(
        status=status,
        reason=_reason_of(status, reading, request.name if request else ""),
        unit_name=request.name if request else "",
        # El payload normalizado viaja como texto y no como estructura porque su destino es un output
        # de job, que es una cadena plana. Serializarlo aquí evita que el adaptador decida el formato.
        normalized_payload=json.dumps(request.model_dump(mode="json"),
                                      ensure_ascii=False) if request else "{}",
        files=skeleton.files,
    )
    log.info("veredicto %s para la unidad %s", outcome.status, outcome.unit_name or "(sin nombre)")
    return outcome


def _status_of(reading: PayloadReading, check: NameCheck) -> ValidationStatus:
    """El orden importa: sin petición no hay nombre que comprobar, así que la forma se mira antes."""
    if reading.request is None:
        return ValidationStatus.MALFORMED_PAYLOAD
    if not check.is_free:
        return ValidationStatus.NAME_TAKEN
    return ValidationStatus.VALID


def _reason_of(status: ValidationStatus, reading: PayloadReading, name: str) -> str:
    if status is ValidationStatus.MALFORMED_PAYLOAD:
        return (_REASON[status] % reading.detail).strip()
    if status is ValidationStatus.NAME_TAKEN:
        return _REASON[status] % name
    return ""
