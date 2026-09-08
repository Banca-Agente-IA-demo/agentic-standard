"""En qué punto del ciclo de vida está una unidad, leído de sus lanzamientos.

El estado no se declara: se deriva. Los tres que se pueden derivar de los lanzamientos son los del
lineamiento del ciclo de vida, con su valor técnico en inglés: `development` mientras no hay nada
publicado, `experimental` cuando todo lo publicado son prelanzamientos, y `production` en cuanto
existe una versión final.

Hay un cuarto resultado que **no** es un estado del ciclo de vida, y por eso no lleva ninguno de sus
seis nombres: `indeterminate`. Suspender y retirar una unidad ponen sus lanzamientos en borrador, así
que una unidad suspendida o retirada tiene cero lanzamientos publicados y se leería como
`development`. Responder «en desarrollo: nada que deprecar» a quien tiene una unidad suspendida es
decirle algo falso. Distinguirlas necesita la ficha del catálogo, que esta capacidad no lee, así que
lo que hace es no afirmar.

Puro: recibe los lanzamientos ya leídos.
"""

from __future__ import annotations

from dataclasses import dataclass

from authoring_core.domain.release_tags import Release, version_in
from authoring_core.domain.versions import Version, highest

STATE_DEVELOPMENT = "development"
STATE_EXPERIMENTAL = "experimental"
STATE_PRODUCTION = "production"
STATE_INDETERMINATE = "indeterminate"

NOTHING_TO_DEPRECATE = "En desarrollo: nada que deprecar"
MAY_BE_WITHDRAWN = (
    "esta unidad no tiene ninguna versión publicada, pero sí lanzamientos en borrador: puede estar "
    "suspendida o retirada. Compruébalo en el catálogo antes de seguir"
)


@dataclass(frozen=True)
class UnitState:
    """Lo que el diálogo necesita saber antes de ofrecer el camino de la obsolescencia."""

    state: str
    latest: Version | None = None
    has_final: bool = False
    prerelease_in_flight: bool = False
    message: str | None = None

    @property
    def can_be_deprecated(self) -> bool:
        """Sólo se deprecan unidades en experimental o producción, y la unidad entera."""
        return self.state in (STATE_EXPERIMENTAL, STATE_PRODUCTION)


def classify(releases: tuple[Release, ...], unit: str) -> UnitState:
    """El estado de esa unidad a partir de sus lanzamientos."""
    published = _versions_of(releases, unit, drafts=False)
    if not published:
        return _nothing_published(releases, unit)
    latest = highest(published)
    finals = tuple(version for version in published if version.is_final)
    return UnitState(
        state=STATE_PRODUCTION if finals else STATE_EXPERIMENTAL,
        latest=latest,
        has_final=bool(finals),
        # Una versión nueva nace experimental y convive con la de producción, así que la unidad sigue
        # en producción mientras exista una final. Que haya una beta por delante es un dato aparte.
        prerelease_in_flight=bool(finals) and latest is not None and not latest.is_final,
    )


def _nothing_published(releases: tuple[Release, ...], unit: str) -> UnitState:
    if _versions_of(releases, unit, drafts=True):
        return UnitState(state=STATE_INDETERMINATE, message=MAY_BE_WITHDRAWN)
    return UnitState(state=STATE_DEVELOPMENT, message=NOTHING_TO_DEPRECATE)


def _versions_of(releases: tuple[Release, ...], unit: str, *, drafts: bool) -> tuple[Version, ...]:
    return tuple(
        version
        for release in releases
        if release.is_draft is drafts
        for version in (version_in(release.tag, unit),)
        if version is not None
    )
