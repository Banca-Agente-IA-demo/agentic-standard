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
    "<<TEAM_MAILBOX>>": "squad-demo@bcp.com.pe",
    # `high` y no `medium`: la unidad de prueba que instancian las plantillas lleva servidor MCP con
    # credenciales, y eso da un mínimo calculado de `high`. El campo sólo puede elevar, así que este
    # valor vale para todas las plantillas, con servidor y sin él.
    "<<RISK_LEVEL>>": "high",
    "<<SERVER>>": "jira",
    # El `selfcheck.py` del paquete de diseño no instanciaba `.mcp.json`, así que este marcador no
    # tenía valor de prueba; lo descubrió esta suite al ampliar la instanciación a esa plantilla.
    "<<URL>>": "https://jira.bcp.com.pe/mcp",
    "<<CREDENTIAL>>": "JIRA_TOKEN",
    "<<ACCOUNTABLE_TEAM>>": "platform-atlassian",
    # `<<TOOLS_DIGEST>>` se retiró el 17 de septiembre de 2026: el digest dejó de ser un marcador de
    # plantilla al mudarse dentro de `tools_contract`, que escribe entero el asistente y la plantilla
    # ya no emite. Un marcador para algo que nadie teclea sugería que alguien debía teclearlo.
}

# Plantillas estructuradas: las que se instancian entero y se validan. El manifiesto es UNO para las
# dos formas de unidad, porque lo único que cambia entre ellas es el directorio de destino.
STRUCTURED_TEMPLATES = (
    "unit/plugin.json",
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
