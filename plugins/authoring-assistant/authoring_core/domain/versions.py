"""La versión de una unidad: cómo se lee, cómo se ordena y cuál es la siguiente.

Las reglas de versión fijan tres cosas que aquí son código: toda versión nace con sufijo de
prelanzamiento; la propuesta es estrictamente mayor que la última publicada, con la precedencia que
corresponde a los prelanzamientos; y al subir un número los de la derecha vuelven a cero.

Puro: recibe cadenas y devuelve versiones. No sabe de dónde salen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from authoring_core.domain.diff_rules import Level

PRERELEASE_LABEL = "beta"
FIRST_VERSION_OF_A_NEW_UNIT = "0.1.0-beta.1"

# Sin metadatos de compilación, igual que el esquema del marketplace: no se usan y ordenarlos no
# está definido.
_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-" + PRERELEASE_LABEL + r"\.(\d+))?$")


class VersionError(ValueError):
    """La cadena no es una versión que estas reglas sepan tratar."""


@dataclass(frozen=True, order=True)
class Version:
    """Una versión ordenable. Un prelanzamiento va antes que la final del mismo número."""

    major: int
    minor: int
    patch: int
    # Una versión final es mayor que cualquiera de sus prelanzamientos, así que el ausente ordena
    # después de todos ellos. Con un contador imposible de alcanzar sale sin caso especial.
    prerelease: int = 0

    @property
    def is_final(self) -> bool:
        return self.prerelease == _NO_PRERELEASE

    def __str__(self) -> str:
        number = f"{self.major}.{self.minor}.{self.patch}"
        return number if self.is_final else f"{number}-{PRERELEASE_LABEL}.{self.prerelease}"


_NO_PRERELEASE = 1 << 30


def parse(text: str) -> Version:
    """La versión que dice la cadena, o un error de dominio si no la dice."""
    match = _VERSION.match(text.strip())
    if match is None:
        raise VersionError(f"no es una versión válida de una unidad: {text!r}")
    major, minor, patch, prerelease = match.groups()
    return Version(
        major=int(major),
        minor=int(minor),
        patch=int(patch),
        prerelease=int(prerelease) if prerelease is not None else _NO_PRERELEASE,
    )


def parse_or_none(text: str) -> Version | None:
    """Igual, pero una etiqueta que no es una versión se descarta en vez de detenerlo todo."""
    try:
        return parse(text)
    except VersionError:
        return None


def highest(versions: tuple[Version, ...]) -> Version | None:
    """La mayor de todas, o `None` si no hay ninguna."""
    return max(versions) if versions else None


def next_version(current: Version | None, published: Version | None, level: Level) -> Version:
    """La versión que sigue: siempre en prelanzamiento y siempre por delante de lo publicado.

    `current` es la de la rama principal y `published` la última publicada. Pueden diferir: la
    principal puede ir por delante con un prelanzamiento que todavía no ha salido.
    """
    if published is None:
        # Sin nada publicado no hay a quien romperle nada, y la unidad se queda en la versión inicial
        # sea cual sea el nivel. Si la principal ya iba por delante se respeta: retroceder el
        # manifiesto sería peor que no moverlo.
        return _greater_of(current, parse(FIRST_VERSION_OF_A_NEW_UNIT))
    # Con algo publicado se cuenta desde la mayor de las dos, y por eso la propuesta avanza siempre:
    # si la principal va por detrás de lo publicado, porque alguien publicó desde otra rama, contar
    # desde ella daría una versión que ya existe con otro contenido.
    return _raise_from(current, published, level)


def _raise_from(current: Version | None, published: Version, level: Level) -> Version:
    reference = _greater_of(current, published)
    if _continues_the_prerelease(reference, current, level):
        return Version(reference.major, reference.minor, reference.patch, reference.prerelease + 1)
    return _bumped(reference, level)


def _continues_the_prerelease(reference: Version, current: Version | None, level: Level) -> bool:
    """Un prelanzamiento en vuelo absorbe los cambios de su nivel o inferiores.

    Uno de nivel superior sube el número que toca y el contador vuelve a empezar.
    """
    if reference.is_final or current is None or current.is_final:
        return False
    return not _exceeds(level, _level_reached_by(current))


def _bumped(version: Version, level: Level) -> Version:
    """Sube el número que toca; los de la derecha vuelven a cero y el contador empieza."""
    if level is Level.MAJOR:
        return Version(version.major + 1, 0, 0, 1)
    if level is Level.MINOR:
        return Version(version.major, version.minor + 1, 0, 1)
    return Version(version.major, version.minor, version.patch + 1, 1)


def _level_reached_by(version: Version) -> Level:
    """Qué salto representa el prelanzamiento en vuelo respecto de la versión anterior."""
    if version.minor == 0 and version.patch == 0:
        return Level.MAJOR
    if version.patch == 0:
        return Level.MINOR
    return Level.PATCH


_RANK = {Level.PATCH: 0, Level.MINOR: 1, Level.MAJOR: 2}


def _exceeds(level: Level, reached: Level) -> bool:
    return _RANK[level] > _RANK[reached]


def is_at_least(chosen: Level, minimum: Level) -> bool:
    """El autor puede subir por encima del mínimo, nunca por debajo."""
    return _RANK[chosen] >= _RANK[minimum]


def _greater_of(one: Version | None, other: Version | None) -> Version | None:
    if one is None:
        return other
    if other is None:
        return one
    return max(one, other)
