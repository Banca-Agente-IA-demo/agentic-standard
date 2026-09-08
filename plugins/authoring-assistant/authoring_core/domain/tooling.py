"""Se hace cargo de decidir si la máquina del autor tiene lo que el asistente necesita.

Puro: recibe lo observado de cada herramienta y decide. Quien mira la máquina es un adaptador.

Se comprueba antes de la primera pregunta. Fallar a mitad del diálogo, cuando el autor ya ha
contestado cinco veces, es peor que no empezar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

STATE_OK = "ok"
STATE_MISSING_TOOL = "missing_tool"

# El suelo que declara el estándar. Vive aquí como constante nombrada porque es una palanca de
# comportamiento: subirla deja fuera máquinas que hoy funcionan.
MINIMUM_PYTHON = (3, 11)


@dataclass(frozen=True)
class ToolObservation:
    """Lo visto de una herramienta concreta, sin juzgar todavía."""

    name: str
    present: bool
    version: tuple[int, ...] | None = None
    authenticated: bool | None = None
    """Sólo para las herramientas que además necesitan una sesión abierta."""
    how_to_fix: str = ""


@dataclass(frozen=True)
class ToolingState:
    state: str
    missing: tuple[str, ...] = ()
    message: str | None = None
    details: tuple[str, ...] = field(default_factory=tuple)

    @property
    def can_continue(self) -> bool:
        return self.state == STATE_OK


def _problem_with(tool: ToolObservation) -> str | None:
    """Qué le pasa a esta herramienta, o `None` si no le pasa nada."""
    if not tool.present:
        return f"falta {tool.name}"
    if tool.name == "python" and tool.version is not None and tool.version < MINIMUM_PYTHON:
        declared = ".".join(str(part) for part in MINIMUM_PYTHON)
        found = ".".join(str(part) for part in tool.version)
        return f"{tool.name} {found} está por debajo del mínimo {declared}"
    if tool.authenticated is False:
        # Estar instalada no basta: sin sesión no puede leer nada de la plataforma.
        return f"{tool.name} no tiene una sesión activa"
    return None


def check(tools: tuple[ToolObservation, ...]) -> ToolingState:
    """Si se puede seguir, y si no, qué falta y qué hacer con cada cosa."""
    problems = [(tool, problem) for tool in tools if (problem := _problem_with(tool)) is not None]
    if not problems:
        return ToolingState(state=STATE_OK)
    return ToolingState(
        state=STATE_MISSING_TOOL,
        missing=tuple(tool.name for tool, _ in problems),
        message="El asistente no puede empezar: " + "; ".join(problem for _, problem in problems) + ".",
        details=tuple(tool.how_to_fix for tool, _ in problems if tool.how_to_fix),
    )
