"""El único puerto del asistente: de dónde salen las versiones publicadas de una unidad.

Existe porque es lo único de esta capacidad que necesita red. Con él, las reglas se prueban con un
doble y la suite corre sin salir de la máquina. Todo lo demás (git, el sistema de archivos, las
herramientas de la máquina) tiene implementación única y va sin puerto.

El tipo que viaja por el puerto es del dominio: el contrato es de quién lo sirve, no del dato.
"""

from __future__ import annotations

from typing import Protocol

from authoring_core.domain.release_tags import Release


class ReleaseProvider(Protocol):
    """Los lanzamientos de una unidad, en cualquier orden."""

    def list_releases(self, unit: str) -> tuple[Release, ...]: ...
