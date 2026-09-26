"""Banda de orquestación de create-unit. Aquí no se decide nada: el paso decide si siembra.

Qué cubre y qué no. Escribe el esqueleto bajo la raíz de trabajo. No crea ramas, no hace commit y
no empuja: eso es del job que tiene permiso de escritura.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md E2 y E3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from create_unit.orchestration_sub_process.steps.write_unit_skeleton import write_unit_skeleton

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from create_unit.commons.models.seams import NameCheck, SeededSkeleton

__all__ = ["run_orchestration_sub_process"]


def run_orchestration_sub_process(check: NameCheck, templates: Path,
                                  root: Path) -> SeededSkeleton:
    """Las rutas sembradas, o ninguna."""
    return write_unit_skeleton(check, templates, root)
