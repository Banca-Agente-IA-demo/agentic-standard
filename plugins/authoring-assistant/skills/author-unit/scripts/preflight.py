"""Comprueba que la máquina del autor tiene lo que el asistente necesita.

Se ejecuta antes de la primera pregunta. Fallar a mitad del diálogo, cuando el autor ya ha contestado
cinco veces, es peor que no empezar.

Estados: ok, missing_tool.
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, without_nulls  # noqa: E402  (ajusta sys.path)

from authoring_core.application.author_context import check_tooling  # noqa: E402


def main() -> int:
    configure_streams()
    state = check_tooling()
    return emit(
        without_nulls(
            {
                "state": state.state,
                "missing": list(state.missing),
                "message": state.message,
                "details": list(state.details),
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main())
