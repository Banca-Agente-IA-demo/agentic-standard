"""Siembra el esqueleto de una unidad publicable a partir del formulario de autoservicio de Port.

Vive junto a las plantillas y no en el repositorio de dominio a propósito: si cada dominio tuviera su
generador, con el tiempo producirían unidades distintas y nadie sabría cuál es la forma buena. El
workflow del dominio hace checkout de este repositorio y ejecuta el entry point `tools/seed_unit.py`.

Los cinco módulos, de la frontera hacia dentro:

| Módulo | Qué hace |
|---|---|
| `unit_kinds` | Los conjuntos cerrados: forma, tipo de artefacto y nivel de riesgo |
| `unit_request` | La frontera exterior: valida el JSON del formulario y lo convierte en dominio |
| `unit_layout` | Dónde va cada cosa dentro de la unidad. Puro |
| `unit_manifest` | El manifiesto y el `.mcp.json`, desde la plantilla. Puro |
| `write_unit` | El único que toca disco |
| `errors` | La jerarquía de errores del dominio |
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
