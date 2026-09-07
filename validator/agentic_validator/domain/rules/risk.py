"""Nivel de riesgo: el mínimo se calcula de hechos y el autor sólo puede elevarlo (03 §1).

El nivel decide quién más aprueba y cuánto dura esa aprobación, así que declararlo por debajo de los
hechos salta aprobadores obligatorios.
"""

from __future__ import annotations

from agentic_validator.domain.model import (
    GOVERNANCE_FILE,
    SENSITIVE_CLASSIFICATIONS,
    Finding,
    RiskLevel,
    UnitSnapshot,
    error,
)


def minimum_risk(snapshot: UnitSnapshot) -> RiskLevel:
    """El mínimo derivado de hechos declarados y de lo que hay en el árbol.

    Alto: el servidor escribe fuera del cliente, hay credenciales, o el dato es sensible.
    Medio: la unidad ejecuta código propio sin invocación, o usa un servidor sólo de lectura.
    Bajo: ninguna de las anteriores.
    """
    governance = snapshot.governance or {}
    if str(governance.get("data_classification") or "") in SENSITIVE_CLASSIFICATIONS:
        return RiskLevel.HIGH
    block = governance.get("mcp")
    if isinstance(block, dict):
        for server in block.values():
            if not isinstance(server, dict):
                continue
            if server.get("write_operations") is True:
                return RiskLevel.HIGH
            if server.get("credentials"):
                return RiskLevel.HIGH
    if snapshot.has_hooks or snapshot.has_mcp:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def check_declared_risk_is_not_lower(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El campo es opcional y sólo sirve para elevar."""
    governance = snapshot.governance
    if governance is None:
        return ()
    declared_value = governance.get("risk_level")
    if declared_value is None:
        return ()
    try:
        declared = RiskLevel(str(declared_value))
    except ValueError:
        return ()  # el enumerado lo impone el contrato
    computed = minimum_risk(snapshot)
    if declared.rank < computed.rank:
        return (
            error(
                "risk.declared-below-computed",
                GOVERNANCE_FILE,
                f"declara riesgo {declared.value!r} y los hechos dan un mínimo de {computed.value!r}; el campo sólo eleva",
            ),
        )
    return ()
