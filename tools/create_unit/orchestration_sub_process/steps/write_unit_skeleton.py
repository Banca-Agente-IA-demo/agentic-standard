"""Paso 5 de create-unit · escribe en disco.

Sembrar el esqueleto de la unidad bajo la raíz de trabajo, desde las plantillas del estándar.

NO EMPUJA NADA, NO CREA RAMAS Y NO HABLA CON GIT. Escribe archivos bajo `root` y devuelve sus rutas.
El job que tiene permiso de escritura es otro, y por eso el esqueleto viaja después como artifact:
así el job que decide no necesita `contents: write`.

NO REIMPLEMENTA LA SIEMBRA. Llama a `write_unit`, que es el mismo sembrador probado que ya usaba el
flujo anterior. Aquí solo se decide SI se siembra.

NO SIEMBRA CUANDO NO SE PUEDE, y esa decisión vive aquí y no en el compositor, porque un compositor
que ramifica sobre el contenido de un sello deja de ser un compositor (E3). La condición no se
escribe dos veces: la declara `NameCheck.can_seed` (C4).

EL ESQUELETO NO PASA EL GATE, y es correcto. Una unidad en Desarrollo debe fallarlo: no tiene
descripciones reales ni casos de evals. Lo que no puede es PARECER terminada.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 4 y 5. AGENTS.md E3, C4, S5 y S6.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from create_unit.commons.models.seams import SeededSkeleton
from unit_seed.write_unit import write_unit

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

    from create_unit.commons.models.seams import NameCheck

__all__ = ["write_unit_skeleton"]

log = logging.getLogger(__name__)


def write_unit_skeleton(check: NameCheck, templates: Path, root: Path) -> SeededSkeleton:
    """Las rutas sembradas, relativas a `root`. Vacías cuando no había nada que sembrar."""
    request = check.request
    # La segunda mitad de la condición es para el verificador de tipos y no una comprobación nueva:
    # `can_seed` ya exige que la petición exista, pero el verificador no lo deduce de una propiedad.
    if not check.can_seed or request is None:
        log.debug("no se siembra: el formulario no llego a un estado sembrable")
        return SeededSkeleton(files=())
    written = write_unit(request, templates, root)
    files = tuple(str(path.relative_to(root).as_posix()) for path in written)
    for path in files:
        log.info("sembrado %s", path)
    return SeededSkeleton(files=files)
