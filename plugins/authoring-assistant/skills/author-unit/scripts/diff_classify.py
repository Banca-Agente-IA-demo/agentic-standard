"""Dice qué salto de versión exige el cambio de una unidad, y por qué.

Lee el diff acotado a la carpeta de la unidad y lo clasifica contra la tabla de las reglas de versión.
No mira los lanzamientos y no propone versión: eso es `version_bump.py`.

Uso: diff_classify.py <unidad>
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, fail, without_nulls  # noqa: E402  (ajusta sys.path)

from authoring_core.adapters.git import GitUnavailable  # noqa: E402
from authoring_core.adapters.units import UnitNotFound, root_of  # noqa: E402
from authoring_core.application.version_planning import classify_diff  # noqa: E402

USAGE = "uso: diff_classify.py <unidad>"


def as_document(classification) -> dict:
    """La clasificación, en la forma que el diálogo consume."""
    return without_nulls(
        {
            "state": "empty" if classification.is_empty else "classified",
            "minimum": classification.minimum.value if classification.minimum else None,
            "reasons": [
                without_nulls(
                    {
                        "level": reason.level.value,
                        "path": reason.path,
                        "key": reason.key,
                        "explanation": reason.explanation,
                    }
                )
                for reason in classification.reasons
            ],
            "message": "el cambio está vacío: no hay nada que versionar" if classification.is_empty else None,
        }
    )


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return fail(f"falta el nombre de la unidad. {USAGE}")
    try:
        return emit(as_document(classify_diff(root_of(args[0]))))
    except (UnitNotFound, GitUnavailable) as failure:
        return fail(str(failure))


if __name__ == "__main__":
    sys.exit(main())
