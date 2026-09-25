"""Jerarquía de errores del sembrador de unidades.

Por qué existe. X1 pide una base propia del dominio para poder capturar a distintos niveles sin caer
en `except Exception`. La versión anterior tenía una sola clase colgando de `ValueError`, y el
`except (OSError, ValueError)` del entry point tragaba también los `ValueError` genuinos del
intérprete y los reportaba como un fallo de siembra.

Qué cubre y qué no. Solo lo que impide sembrar. Lo que el validador detecta sobre una unidad ya
escrita no pasa por aquí: eso son hallazgos, no excepciones (X2).

Trazabilidad. AGENTS.md X1, X2 y P2.
"""

from __future__ import annotations

__all__ = ["SeedError", "InvalidRequestError", "TemplateNotFoundError"]


class SeedError(Exception):
    """Base del dominio del sembrador. Captura todo lo nuestro sin capturar bugs."""


class InvalidRequestError(SeedError):
    """Los datos del formulario no describen una unidad que se pueda sembrar."""


class TemplateNotFoundError(SeedError):
    """Falta la plantilla de la que tendría que salir un artefacto."""
