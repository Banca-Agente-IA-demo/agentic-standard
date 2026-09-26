"""Los sellos entre las cuatro bandas del paso de creación.

Por qué son dataclasses y no modelos pydantic. No salen del proceso y no se serializan: lo que se
les pide es estructura e inmutabilidad, «que una banda no reescriba lo que otra cerró» (C2). El
único que cruza al exterior es `CreationOutcome`, y lo serializa el adaptador de la línea de
órdenes, no este módulo.

Por qué `request` puede faltar. Un formulario mal formado no produce petición, y la banda siguiente
tiene que poder distinguir «no hay petición» de «hay una petición vacía», que no son lo mismo (P7).
Por eso `None` y no un `UnitRequest` con los campos en blanco.

Qué cubre y qué no. Declara qué viaja. No decide nada: quien decide son los pasos.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md C2, C4, C8 y P7.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from create_unit.commons.enums.validation_status import ValidationStatus

if TYPE_CHECKING:  # pragma: no cover
    from unit_seed.unit_request import UnitRequest

__all__ = ["PayloadReading", "NameCheck", "SeededSkeleton", "CreationOutcome"]


@dataclass(frozen=True, slots=True)
class PayloadReading:
    """Lo que deja la banda de entrada: la petición, o el motivo por el que no hay ninguna."""

    request: UnitRequest | None
    detail: str


@dataclass(frozen=True, slots=True)
class NameCheck:
    """Lo que deja la banda previa: la petición con el equipo resuelto y si su nombre está libre."""

    request: UnitRequest | None
    is_free: bool

    @property
    def can_seed(self) -> bool:
        """Las dos condiciones para sembrar, escritas UNA sola vez.

        Vive aquí y no en el paso que siembra porque el paso que compone la respuesta necesita la
        misma distinción, y la misma lógica en dos lugares se extrae sin atenuantes (C4).
        """
        return self.request is not None and self.is_free


@dataclass(frozen=True, slots=True)
class SeededSkeleton:
    """Lo que deja la banda de orquestación: las rutas sembradas, relativas a la raíz.

    Vacía cuando no se sembró, y vacía es un resultado legítimo: no se devuelve `None` para decir
    «no había nada que sembrar», porque quien lo lee tendría que ramificar antes de contar (P7).
    """

    files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreationOutcome:
    """Lo que deja la banda de salida, y lo único que el adaptador escribe a stdout.

    Tiene siempre las mismas cinco claves, valga lo que valga `status`. Un contrato que cambia de
    forma según el resultado obliga a quien lo lee a mirar primero el estado para saber qué campos
    existen.
    """

    status: ValidationStatus
    reason: str
    unit_name: str
    normalized_payload: str
    files: tuple[str, ...]
