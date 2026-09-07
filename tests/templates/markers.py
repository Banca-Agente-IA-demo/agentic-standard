"""Marcadores de las plantillas y su instanciación con valores de prueba.

La forma `<<NOMBRE>>` se eligió para que un marcador olvidado sea un error visible y localizable con
una expresión regular trivial, no un valor plausible. Este módulo es también la lista de la que puede
partir el asistente de autoría del hito 2.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"

MARKER_PATTERN = re.compile(r"<<[A-Z_]+>>")

# Valores de prueba de los marcadores que aparecen en las plantillas ESTRUCTURADAS (gobierno,
# identidad y bloque del servidor). Los de las plantillas de texto son prosa que rellena el autor y no
# se instancian aquí: esas se comprueban leyendo su frontmatter.
TEST_VALUES = {
    "<<NAME>>": "demo-unit",
    "<<REPO>>": "agents-demo",
    "<<ORG>>": "Banca-Agente-IA-demo",
    "<<VERSION>>": "0.1.0-beta.1",
    "<<DESCRIPTION>>": "Unidad de prueba.",
    "<<TEAM>>": "squad-demo",
    "<<CONTACT>>": "squad-demo@bcp.com.pe",
    "<<EXTERNAL_CONTENT>>": "No procesa contenido externo.",
    "<<SERVER>>": "jira",
    # El `selfcheck.py` del paquete de diseño no instanciaba `.mcp.json`, así que este marcador no
    # tenía valor de prueba; lo descubrió esta suite al ampliar la instanciación a esa plantilla.
    "<<URL>>": "https://jira.bcp.com.pe/mcp",
    "<<CREDENTIAL>>": "JIRA_TOKEN",
    "<<CUSTODIAN_TEAM>>": "plataforma-atlassian",
    "<<ACCESS_REQUEST_URL>>": "https://servicedesk.bcp.com.pe/accesos/jira-api",
    "<<TOOLS_DIGEST>>": "0" * 64,
}

# Plantillas estructuradas: las que se instancian entero y se validan.
STRUCTURED_TEMPLATES = (
    "plugin-unit/GOVERNANCE.json",
    "plugin-unit/.claude-plugin/plugin.json",
    "individual-unit/GOVERNANCE.json",
    "individual-unit/.claude-plugin/plugin.json",
    "artifacts/mcp/mcp-governance-block.json",
    "artifacts/mcp/.mcp.json",
)


class MissingMarkerValue(AssertionError):
    """Una plantilla usa un marcador para el que no hay valor de prueba."""


def read_template(relative_path: str) -> str:
    return (TEMPLATES_DIR / relative_path).read_text(encoding="utf-8")


def instantiate(text: str) -> str:
    """Sustituye cada marcador por su valor de prueba y falla si queda alguno sin cubrir."""
    for marker, value in TEST_VALUES.items():
        text = text.replace(marker, value)
    leftover = sorted(set(MARKER_PATTERN.findall(text)))
    if leftover:
        raise MissingMarkerValue(f"marcadores sin valor de prueba: {leftover}")
    return text
