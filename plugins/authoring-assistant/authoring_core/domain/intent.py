"""Se hace cargo de qué es una intención pendiente válida y qué se hace con una que no lo es.

Puro. Dónde se guarda es cosa del adaptador; aquí sólo se decide si lo guardado sirve para retomar.

La intención existe para que detenerse no cueste el trabajo hecho: el autor ya eligió qué hacer y
sobre qué, y al volver se le propone en vez de preguntárselo otra vez.
"""

from __future__ import annotations

from dataclasses import dataclass

from authoring_core.domain.git_state import Action

VALID_ACTIONS = tuple(action.value for action in Action)


@dataclass(frozen=True)
class Intent:
    pending: bool
    action: Action | None = None
    unit: str | None = None
    message: str | None = None
    """Por qué lo guardado no sirve, cuando no sirve."""


NOTHING_PENDING = Intent(pending=False)


def interpret(stored_action: str | None, stored_unit: str | None) -> Intent:
    """Qué se puede retomar con lo que hay guardado.

    Una acción que no es ninguna de las válidas no se da por buena: llevar el diálogo por un camino
    que el autor no eligió es peor que volver a preguntárselo.

    Una acción sin unidad **sí** cuenta como pendiente: el autor eligió qué hacer aunque todavía no
    sobre qué, y esa mitad de la respuesta no hay que repetirla.
    """
    if not stored_action:
        return NOTHING_PENDING
    if stored_action not in VALID_ACTIONS:
        return Intent(
            pending=False,
            unit=stored_unit or None,
            message=(
                f"La intención guardada dice `{stored_action}`, que no es ninguna de las acciones "
                f"({', '.join(VALID_ACTIONS)}). Se ignora y se vuelve a preguntar."
            ),
        )
    return Intent(pending=True, action=Action(stored_action), unit=stored_unit or None)
