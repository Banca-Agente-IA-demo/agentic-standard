"""Propone la versión que sale del cambio y, si se le pide, la escribe.

Sin `--apply` no toca nada: el diálogo enseña la propuesta y el autor elige. Con `--apply <nivel>`
escribe la versión en el manifiesto de la unidad y en ningún otro archivo. Un nivel por debajo del
mínimo se rechaza.

Uso: version_bump.py <unidad> [--apply <nivel>]
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, fail, without_nulls  # noqa: E402  (ajusta sys.path)

from diff_classify import as_document as classification_document  # noqa: E402

from authoring_core.adapters.git import GitUnavailable  # noqa: E402
from authoring_core.adapters.manifest import ManifestError  # noqa: E402
from authoring_core.adapters.releases import ReleasesUnavailable  # noqa: E402
from authoring_core.adapters.units import UnitNotFound, root_of  # noqa: E402
from authoring_core.application.version_planning import (  # noqa: E402
    UnknownLevel,
    VersionChoiceError,
    apply_version,
    plan_version,
)
from authoring_core.domain.diff_rules import Level  # noqa: E402

USAGE = "uso: version_bump.py <unidad> [--apply <nivel>]"
APPLY_FLAG = "--apply"


def _document(plan, written=None) -> dict:
    return without_nulls(
        {
            **classification_document(plan.classification),
            "unit": plan.unit,
            "current": str(plan.current) if plan.current else None,
            "latest_published": str(plan.latest_published) if plan.latest_published else None,
            "proposed": str(plan.proposed) if plan.proposed else None,
            "is_new_unit": plan.is_new_unit,
            "written_to": written,
        }
    )


def _level(name: str) -> Level:
    try:
        return Level(name)
    except ValueError as failure:
        valid = ", ".join(level.value for level in Level)
        raise UnknownLevel(f"nivel desconocido: {name!r}; los válidos son {valid}") from failure


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return fail(f"falta el nombre de la unidad. {USAGE}")
    unit = args[0]
    rest = args[1:]
    try:
        unit_root = root_of(unit)
        if not rest:
            return emit(_document(plan_version(unit_root, unit)))
        if rest[0] != APPLY_FLAG or len(rest) < 2:
            return fail(f"argumento no reconocido: {' '.join(rest)}. {USAGE}")
        plan, written = apply_version(unit_root, unit, _level(rest[1]))
        return emit(_document(plan, written=str(written)))
    except (UnitNotFound, GitUnavailable, ReleasesUnavailable, ManifestError, VersionChoiceError) as failure:
        return fail(str(failure))


if __name__ == "__main__":
    sys.exit(main())
