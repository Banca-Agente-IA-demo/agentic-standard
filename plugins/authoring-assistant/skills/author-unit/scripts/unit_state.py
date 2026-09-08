"""Dice en qué punto del ciclo de vida está una unidad, para saber si hay algo que deprecar.

Sólo se deprecan unidades en experimental o producción, y se depreca la unidad entera, no una versión
ni un canal. El estado no se declara: se deriva de lo publicado.

Uso: unit_state.py <unidad>
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, fail, without_nulls  # noqa: E402  (ajusta sys.path)

from authoring_core.adapters.releases import ReleasesUnavailable  # noqa: E402
from authoring_core.application.unit_lifecycle import read_unit_state  # noqa: E402

USAGE = "uso: unit_state.py <unidad>"


def as_document(state) -> dict:
    """El estado, en la forma que el diálogo consume."""
    return without_nulls(
        {
            "state": state.state,
            "latest": str(state.latest) if state.latest else None,
            "has_final": state.has_final,
            "prerelease_in_flight": state.prerelease_in_flight,
            "can_be_deprecated": state.can_be_deprecated,
            "message": state.message,
        }
    )


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return fail(f"falta el nombre de la unidad. {USAGE}")
    try:
        return emit(as_document(read_unit_state(args[0])))
    except ReleasesUnavailable as failure:
        return fail(str(failure))


if __name__ == "__main__":
    sys.exit(main())
