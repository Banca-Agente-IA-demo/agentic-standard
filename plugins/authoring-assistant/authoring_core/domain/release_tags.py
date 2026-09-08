"""De las etiquetas de los lanzamientos a la última versión publicada de una unidad.

La etiqueta copia la versión: `<unidad>--v<version>` en un repositorio con varias unidades, y
`v<version>` si aloja una sola. Un borrador no es una publicación y no cuenta.

Puro: recibe los lanzamientos ya leídos.
"""

from __future__ import annotations

from dataclasses import dataclass

from authoring_core.domain.versions import Version, highest, parse_or_none

TAG_PREFIX = "v"
UNIT_SEPARATOR = "--"


@dataclass(frozen=True)
class Release:
    """Un lanzamiento tal y como lo devuelve quien los guarda."""

    tag: str
    is_draft: bool


def latest_published(releases: tuple[Release, ...], unit: str) -> Version | None:
    """La versión publicada más alta de esa unidad, o `None` si no hay ninguna."""
    return highest(
        tuple(
            version
            for release in releases
            if not release.is_draft
            for version in (version_in(release.tag, unit),)
            if version is not None
        )
    )


def version_in(tag: str, unit: str) -> Version | None:
    """La versión que lleva la etiqueta si es de esa unidad, y `None` si no lo es.

    Una etiqueta de otra unidad del mismo repositorio se descarta aquí: mezclarlas daría a una unidad
    la versión de su vecina.
    """
    if UNIT_SEPARATOR in tag:
        owner, _, rest = tag.partition(UNIT_SEPARATOR)
        return parse_or_none(_without_prefix(rest)) if owner == unit else None
    return parse_or_none(_without_prefix(tag))


def tag_for(version: Version, unit: str, *, alone_in_repository: bool) -> str:
    """La etiqueta que le corresponde a esa versión."""
    number = f"{TAG_PREFIX}{version}"
    return number if alone_in_repository else f"{unit}{UNIT_SEPARATOR}{number}"


def _without_prefix(text: str) -> str:
    return text[len(TAG_PREFIX) :] if text.startswith(TAG_PREFIX) else text
