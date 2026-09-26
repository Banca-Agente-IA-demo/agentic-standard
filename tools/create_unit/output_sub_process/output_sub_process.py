"""Banda de salida de create-unit. Aquí no se calcula nada: el paso compone el veredicto.

Qué cubre y qué no. Traduce los sellos de las bandas anteriores al veredicto que sale del proceso.
No repara nada de lo que encuentra: nombra y enruta (C7).

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md E2, E3 y C7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from create_unit.output_sub_process.steps.compose_validation_status import (
    compose_validation_status)
from create_unit.output_sub_process.steps.write_run_failure import write_run_failure

if TYPE_CHECKING:  # pragma: no cover
    from create_unit.commons.models.seams import (CreationOutcome, NameCheck, PayloadReading,
                                                  SeededSkeleton)
    from port_catalog.client import PortClient

__all__ = ["run_output_sub_process"]


def run_output_sub_process(reading: PayloadReading, check: NameCheck, skeleton: SeededSkeleton,
                           run_id: str, client: PortClient) -> CreationOutcome:
    """El veredicto que el adaptador escribe a stdout, después de haberlo devuelto a Port.

    El aviso va DESPUÉS de componer y no dentro del compositor del veredicto: componer es cálculo y
    avisar es efecto, y mezclarlos haría que la prueba del veredicto necesitara un catálogo.
    """
    outcome = compose_validation_status(reading, check, skeleton)
    write_run_failure(outcome, run_id, client)
    return outcome
