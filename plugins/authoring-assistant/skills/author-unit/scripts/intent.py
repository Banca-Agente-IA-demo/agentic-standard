"""Lee, guarda o borra lo que el autor ya había elegido y sigue pendiente.

Vive en la configuración local del repositorio: no se versiona, no ensucia el árbol y sobrevive a
cerrar la sesión. Es lo que permite retomar sin volver a preguntarlo todo.

Uso: intent.py [get] | intent.py set <accion> [<unidad>] | intent.py clear
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, fail, without_nulls  # noqa: E402  (ajusta sys.path)

from authoring_core.application.author_context import (  # noqa: E402
    forget_intent,
    read_intent,
    remember_intent,
)

USAGE = "uso: intent.py [get] | intent.py set <accion> [<unidad>] | intent.py clear"


def main(argv: list[str] | None = None) -> int:
    configure_streams()
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "get"
    if command == "set":
        if len(args) < 2:
            return fail(f"`set` necesita la acción. {USAGE}")
        intent = remember_intent(args[1], args[2] if len(args) > 2 else None)
    elif command == "clear":
        intent = forget_intent()
    elif command == "get":
        intent = read_intent()
    else:
        return fail(f"comando desconocido: {command!r}. {USAGE}")
    return emit(
        without_nulls(
            {
                "pending": intent.pending,
                "action": intent.action.value if intent.action else None,
                "unit": intent.unit,
                "message": intent.message,
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main())
