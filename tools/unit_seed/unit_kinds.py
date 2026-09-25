"""Los conjuntos cerrados de la siembra: forma de la unidad, tipo de artefacto y nivel de riesgo.

Por qué existe aparte del modelo de la petición. Los módulos que deciden rutas y componen el
manifiesto necesitan estos tipos y no deben arrastrar pydantic: dejarlos aquí mantiene puro todo lo
que cuelga de ellos.

Por qué `StrEnum` y no `Enum`. Los tres valores se leen como texto fuera del intérprete: llegan en el
JSON del formulario de Port y se escriben tal cual en el manifiesto. T1 decide entre los dos
exactamente por eso. Con una cadena suelta, un valor mal escrito no falla: se comporta como una forma
que no existe y toma la rama de ninguna.

Trazabilidad. AGENTS.md T1 y T2. Documento 01 §1 y §2 del entregable E2 para las dos formas y los
cinco tipos; documento 02 §2 para los tres niveles de riesgo.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["UnitForm", "ArtifactType", "RiskLevel", "BEHAVIOURAL_TYPES"]


class UnitForm(StrEnum):
    """Individual se puede revocar sola; agrupada se instala y se suspende entera."""

    INDIVIDUAL = "individual"
    GROUPED = "grouped"


class ArtifactType(StrEnum):
    """Los cinco tipos que una unidad puede contener."""

    SKILL = "skill"
    AGENT = "agent"
    PROMPT = "prompt"
    HOOKS = "hooks"
    MCP = "mcp"


class RiskLevel(StrEnum):
    """Impacto que el autor atribuye a la unidad. Informa al catálogo; no deriva aprobadores."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Los tipos que tienen comportamiento que medir, y por tanto los únicos que llevan suite de evals.
# Se escriben sus miembros y no se derivan de `ArtifactType`: un día alguien añade un tipo al
# enumerado y esta tupla no debe crecer sola (T3). El servidor MCP se comprueba contra su contrato
# declarado y los hooks contra sus pruebas unitarias, así que ninguno de los dos entra.
BEHAVIOURAL_TYPES: tuple[ArtifactType, ...] = (
    ArtifactType.SKILL,
    ArtifactType.AGENT,
    ArtifactType.PROMPT,
)
