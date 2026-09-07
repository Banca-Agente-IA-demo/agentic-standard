"""Lector del frontmatter de un artefacto de texto.

Corto a propósito. El validador de la demo traía una extracción degradada por expresiones regulares
para rescatar un frontmatter con YAML inválido; existía para el ensamblado que el diseño retiró. Aquí
un frontmatter inválido es un hallazgo, no algo que rescatar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import yaml

_DELIMITED = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)


@dataclass(frozen=True)
class ParsedFrontmatter:
    """Ausencia y fallo son cosas distintas: sin frontmatter no hay error que informar."""

    data: dict | None = None
    error: str | None = None


def parse(text: str) -> ParsedFrontmatter:
    delimited = _DELIMITED.match(text)
    if delimited is None:
        return ParsedFrontmatter()
    try:
        parsed = yaml.safe_load(delimited.group(1))
    except yaml.YAMLError as failure:
        return ParsedFrontmatter(error=str(failure).splitlines()[0])
    if not isinstance(parsed, dict):
        return ParsedFrontmatter(error="el frontmatter no es un mapa de claves")
    return ParsedFrontmatter(data=parsed)
