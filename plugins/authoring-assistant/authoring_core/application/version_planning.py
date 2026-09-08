"""El caso de uso que responde qué salto toca y qué versión sale de él.

Las tres entradas de línea de órdenes lo consumen a él: son tres puertas, no tres lecturas del diff.
El proveedor de lanzamientos llega como argumento con un valor por defecto, para que la prueba ponga
un doble sin parchear nada.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from authoring_core.adapters import diff, manifest
from authoring_core.adapters.releases import GitHubReleases
from authoring_core.domain.diff_rules import DiffClassification, Level, classify_changes
from authoring_core.domain.release_tags import latest_published
from authoring_core.domain.versions import Version, is_at_least, next_version, parse_or_none
from authoring_core.ports.releases import ReleaseProvider


class VersionChoiceError(ValueError):
    """El nivel que se pidió aplicar no se puede aplicar."""


class LevelBelowMinimum(VersionChoiceError):
    """El nivel elegido es menor que el que exige el cambio."""


class UnknownLevel(VersionChoiceError):
    """Lo que se pidió aplicar no es ninguno de los tres niveles."""


@dataclass(frozen=True)
class VersionPlan:
    """Lo que el diálogo enseña antes de que el autor elija."""

    unit: str
    current: Version | None
    latest_published: Version | None
    classification: DiffClassification
    proposed: Version | None

    @property
    def is_new_unit(self) -> bool:
        return self.latest_published is None


def classify_diff(unit_root: Path, cwd: Path | None = None) -> DiffClassification:
    """Qué salto exige el cambio de esa unidad. No mira los lanzamientos."""
    return classify_changes(diff.read_changes(unit_root, cwd))


def plan_version(
    unit_root: Path,
    unit: str,
    cwd: Path | None = None,
    *,
    releases: ReleaseProvider | None = None,
) -> VersionPlan:
    """El salto que toca y la versión que saldría de aceptarlo. No escribe nada."""
    classification = classify_diff(unit_root, cwd)
    published = latest_published((releases or GitHubReleases()).list_releases(unit), unit)
    current = parse_or_none(manifest.read_version(unit_root) or "")
    proposed = (
        None
        if classification.minimum is None
        else next_version(current, published, classification.minimum)
    )
    return VersionPlan(
        unit=unit,
        current=current,
        latest_published=published,
        classification=classification,
        proposed=proposed,
    )


def apply_version(
    unit_root: Path,
    unit: str,
    level: Level,
    cwd: Path | None = None,
    *,
    releases: ReleaseProvider | None = None,
) -> tuple[VersionPlan, Path]:
    """Escribe en el manifiesto la versión que sale del nivel elegido.

    El autor puede subir por encima del mínimo; por debajo no, y por eso se comprueba aquí y no en el
    diálogo: quien escribe es quien tiene que negarse.
    """
    plan = plan_version(unit_root, unit, cwd, releases=releases)
    minimum = plan.classification.minimum
    if minimum is None:
        raise LevelBelowMinimum("el cambio está vacío: no hay nada que versionar")
    if not is_at_least(level, minimum):
        raise LevelBelowMinimum(
            f"el nivel elegido ({level.value}) es menor que el que exige el cambio ({minimum.value})"
        )
    chosen = next_version(plan.current, plan.latest_published, level)
    written = manifest.write_version(unit_root, str(chosen))
    return _with_proposal(plan, chosen), written


def _with_proposal(plan: VersionPlan, chosen: Version) -> VersionPlan:
    return VersionPlan(
        unit=plan.unit,
        current=plan.current,
        latest_published=plan.latest_published,
        classification=plan.classification,
        proposed=chosen,
    )
