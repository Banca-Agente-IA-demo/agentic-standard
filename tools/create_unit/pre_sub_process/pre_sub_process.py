"""Banda previa de create-unit. Aquí no se decide nada: cada paso es una función de `steps/`.

Qué cubre y qué no. Encadena las tres preguntas que hay que hacerle al catálogo antes de escribir:
quién es el equipo, qué nombres están ocupados y si el de esta unidad lo está. No interpreta las
respuestas: eso es la banda de salida.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md E2 y E3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from create_unit.commons.models.seams import NameCheck
from create_unit.pre_sub_process.steps.is_unit_name_free import is_unit_name_free
from create_unit.pre_sub_process.steps.read_catalog_units import read_catalog_units
from create_unit.pre_sub_process.steps.read_team_slug import read_team_slug

if TYPE_CHECKING:  # pragma: no cover
    from create_unit.commons.models.seams import PayloadReading
    from port_catalog.client import PortClient

__all__ = ["run_pre_sub_process"]


def run_pre_sub_process(reading: PayloadReading, client: PortClient) -> NameCheck:
    """La petición con el equipo resuelto y si su nombre está libre."""
    resolved = read_team_slug(reading, client)
    catalog = read_catalog_units(resolved, client)
    return NameCheck(request=resolved.request, is_free=is_unit_name_free(resolved, catalog))
