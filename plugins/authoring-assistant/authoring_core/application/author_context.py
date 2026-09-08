"""Los tres casos de uso que el asistente ejecuta antes de la primera pregunta.

Orquestan el dominio a través de los adaptadores y devuelven objetos del dominio. Quien los convierte
en documento estructurado es el script de entrada, que es el composition root.
"""

from __future__ import annotations

from pathlib import Path

from authoring_core.adapters import git, intent_store, tools
from authoring_core.domain import intent as intent_rules
from authoring_core.domain import tooling
from authoring_core.domain.git_state import GitState, classify


def check_tooling() -> tooling.ToolingState:
    """Si la máquina tiene lo que hace falta, antes de preguntar nada."""
    return tooling.check(tools.observe())


def read_git_state(cwd: Path | None = None) -> GitState:
    """En qué estado está el repositorio. No modifica nada."""
    return classify(git.observe(cwd))


def read_intent(cwd: Path | None = None) -> intent_rules.Intent:
    """Qué había elegido el autor y sigue pendiente."""
    return intent_rules.interpret(*intent_store.read(cwd))


def remember_intent(action: str, unit: str | None, cwd: Path | None = None) -> intent_rules.Intent:
    """Guarda lo elegido para que detenerse no cueste el trabajo hecho hasta aquí."""
    intent_store.write(action, unit, cwd)
    return read_intent(cwd)


def forget_intent(cwd: Path | None = None) -> intent_rules.Intent:
    """Borra lo pendiente, que es lo que hay que hacer cuando se completa."""
    intent_store.clear(cwd)
    return read_intent(cwd)
