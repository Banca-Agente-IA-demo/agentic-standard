"""En qué punto del ciclo de vida está una unidad.

Es el único caso de uso que no mira el repositorio del autor para nada: el estado se deriva de lo
publicado, y lo publicado vive fuera. El proveedor llega como argumento con un valor por defecto, para
que la prueba ponga un doble sin parchear nada.
"""

from __future__ import annotations

from authoring_core.adapters.releases import GitHubReleases
from authoring_core.domain.unit_state import UnitState, classify
from authoring_core.ports.releases import ReleaseProvider


def read_unit_state(unit: str, *, releases: ReleaseProvider | None = None) -> UnitState:
    """El estado de la unidad, con lo que el diálogo necesita para anunciarlo."""
    return classify((releases or GitHubReleases()).list_releases(unit), unit)
