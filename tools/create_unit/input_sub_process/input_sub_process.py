"""Banda de entrada de create-unit. Aquí no se calcula nada: cada paso es una función de `steps/`.

Qué cubre y qué no. Dice en qué orden se llama a qué y qué necesita cada paso. No valida, no
ramifica y no toca el catálogo.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md E2 y E3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from create_unit.input_sub_process.steps.read_port_payload import read_port_payload

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from create_unit.commons.models.seams import PayloadReading

__all__ = ["run_input_sub_process"]


def run_input_sub_process(payload_file: Path) -> PayloadReading:
    """Un solo paso hoy, y la banda existe igual: la forma se deduce de la ruta, no del recuento."""
    return read_port_payload(payload_file)
