"""Qué promete el paso de creación: sus salidas, quién las lee y con qué estados puede terminar.

Por qué existe aparte del código que lo cumple. C1: esta información estaba escrita tres veces y en
tres sitios distintos (la acción, los outputs del job y el `if:` del job que escribe), y nada
garantizaba que dijeran lo mismo. Aquí es declaración, no ejecución: se puede cruzar contra el YAML
**sin correr nada**.

POR QUÉ CADA CLAVE DECLARA QUIÉN LA LEE. C6: un contrato no es el esquema completo de una salida, es
la intersección de lo que se promete con lo que alguien consume. Sin el campo `source`, una clave no
tiene justificación para estar declarada, y las cinco salidas que nadie leía del flujo anterior
existían exactamente por eso.

Qué cubre y qué no. Declara la superficie del paso. No declara cómo se calcula nada.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 4 y 7. AGENTS.md C1, C6, C8, P5 y T3.
"""

from __future__ import annotations

from dataclasses import dataclass

from create_unit.commons.enums.validation_status import ValidationStatus

__all__ = ["OutputKey", "StepContract", "CREATE_UNIT_CONTRACT"]


@dataclass(frozen=True, slots=True)
class OutputKey:
    """Una clave que el paso emite. `source` no tiene valor por defecto a propósito (T4, C6)."""

    name: str
    description: str
    source: str


@dataclass(frozen=True, slots=True)
class StepContract:
    """Lo que un paso promete. Se escribe como instancia constante, no como clase por paso (C2)."""

    name: str
    outputs: tuple[OutputKey, ...]
    statuses: tuple[ValidationStatus, ...]


# Los tres estados se escriben con sus miembros y no como `tuple(ValidationStatus)`: un día alguien
# añade un cuarto al enumerado y este contrato no debe crecer solo (T3). Crecer solo significaría
# prometer una rama que ningún job atiende.
CREATE_UNIT_CONTRACT = StepContract(
    name="create-unit",
    outputs=(
        OutputKey(
            name="validation-status",
            description="Cual de los tres desenlaces tuvo el formulario.",
            source="El `if:` del job que escribe, y el step que responde a Port.",
        ),
        OutputKey(
            name="reason",
            description="El motivo legible cuando el estado no es valid. Vacio cuando lo es.",
            source="El step que responde a Port y el resumen de la ejecucion.",
        ),
        OutputKey(
            name="unit-name",
            description="El nombre de la unidad, ya validado.",
            source="El job que escribe, para derivar el nombre de la rama.",
        ),
        OutputKey(
            name="normalized-payload",
            description="El formulario con los campos numerados colapsados y el equipo resuelto.",
            source="El job que escribe, para registrar la ficha en el catalogo.",
        ),
    ),
    statuses=(
        ValidationStatus.VALID,
        ValidationStatus.MALFORMED_PAYLOAD,
        ValidationStatus.NAME_TAKEN,
    ),
)
