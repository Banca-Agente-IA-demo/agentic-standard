"""Encadena las cuatro bandas del paso de creación. Aquí no se decide nada.

Por qué existe. Es el único sitio donde se lee **en qué orden** ocurre la creación de una unidad:
leer el formulario, preguntar al catálogo, sembrar y componer el veredicto. Quien busque qué se
comprueba o cómo se siembra no lo encuentra aquí ni debe.

POR QUÉ NO HAY NINGÚN `if`. Los rombos del diagrama de autoría son decisiones sobre el contenido de
un sello, y un compositor que ramifica sobre contenido deja de ser un compositor (E3). Cada paso
declara en su docstring qué hace cuando la banda anterior no le dejó nada.

POR QUÉ EL CLIENTE DEL CATÁLOGO LLEGA POR ARGUMENTO. Para que la prueba pueda sustituirlo sin
parchear módulos (PR6). No lleva valor por defecto: construirlo aquí escondería el cableado dentro
de la función, que es justo lo que esa regla evita.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 3 y 4. AGENTS.md E2, E3 y PR6.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from create_unit.input_sub_process.input_sub_process import run_input_sub_process
from create_unit.orchestration_sub_process.orchestration_sub_process import (
    run_orchestration_sub_process)
from create_unit.output_sub_process.output_sub_process import run_output_sub_process
from create_unit.pre_sub_process.pre_sub_process import run_pre_sub_process

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from create_unit.commons.models.seams import CreationOutcome
    from port_catalog.client import PortClient

__all__ = ["create_unit"]


def create_unit(payload_file: Path, templates: Path, root: Path, client: PortClient,
                run_id: str) -> CreationOutcome:
    """El veredicto del paso, con el esqueleto ya escrito bajo `root` cuando procede.

    `run_id` baja por la firma **sin valor por defecto**, igual que los presupuestos de T4: con un
    default, una invocación que olvidara pasarlo y otra que decidiera no informar se escribirían
    igual, y nadie podría distinguirlas al leer el código.
    """
    reading = run_input_sub_process(payload_file)
    check = run_pre_sub_process(reading, client)
    skeleton = run_orchestration_sub_process(check, templates, root)
    return run_output_sub_process(reading, check, skeleton, run_id, client)
