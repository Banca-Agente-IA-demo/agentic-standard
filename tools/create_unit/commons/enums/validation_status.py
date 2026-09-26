"""El veredicto del paso de creación: tres valores cerrados, no un booleano con prosa al lado.

Por qué existe. El flujo anterior emitía `status` booleano y un `reason` de texto libre, así que
**quien enrutaba tenía que leer prosa para decidir**. Con el enumerado el motivo ES el valor, y el
texto queda solo para que la persona lo lea en la pantalla de Port.

Por qué `StrEnum` y no `Enum`. El valor sale del proceso: viaja como output del job y lo lee el
`if:` del job que escribe, fuera del intérprete. T1 decide entre los dos exactamente por eso.

Qué cubre y qué no. Los tres desenlaces que hoy alguien atiende de forma distinta. Un cuarto valor
solo entra si alguien declara atenderlo aparte, que es C6 aplicado al enrutado: una rama que nadie
consume no tiene por qué existir.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 4 y 7. AGENTS.md T1, T3 y C6.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["ValidationStatus", "BLOCKING_STATUSES"]


class ValidationStatus(StrEnum):
    """Qué pasó con el formulario, desde el punto de vista de quien tiene que enrutar."""

    VALID = "valid"
    MALFORMED_PAYLOAD = "malformed_payload"
    NAME_TAKEN = "name_taken"


# Los estados que paran el flujo antes de escribir nada. Se escriben sus miembros y no se derivan
# con una comparación contra `VALID`: un día alguien añade un cuarto valor y esta tupla no debe
# crecer sola (T3), porque crecer sola significaría bloquear un caso que nadie decidió bloquear.
BLOCKING_STATUSES: tuple[ValidationStatus, ...] = (
    ValidationStatus.MALFORMED_PAYLOAD,
    ValidationStatus.NAME_TAKEN,
)
