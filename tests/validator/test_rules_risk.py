"""El riesgo mínimo se calcula de hechos y el autor sólo puede elevarlo (03 §1)."""

from __future__ import annotations

import copy

from agentic_validator.domain.standard import RiskLevel
from agentic_validator.domain.rules.risk import check_declared_risk_is_not_lower, minimum_risk

from tests.validator.units import SERVER, hooks_config, snapshot, unit_with_mcp, with_governance


def test_una_unidad_sin_hechos_de_riesgo_tiene_minimo_bajo():
    assert minimum_risk(snapshot()) is RiskLevel.LOW


def test_ejecutar_codigo_propio_sin_invocacion_eleva_el_minimo_a_medio():
    assert minimum_risk(snapshot(hooks=hooks_config())) is RiskLevel.MEDIUM


def test_un_servidor_solo_de_lectura_y_sin_credenciales_eleva_el_minimo_a_medio():
    snap = unit_with_mcp()
    governance = copy.deepcopy(snap.governance)
    governance["mcp"][SERVER]["credentials"] = []
    del governance["mcp"][SERVER]["credentials_owner"]
    assert minimum_risk(snapshot(governance=governance, mcp=snap.mcp)) is RiskLevel.MEDIUM


def test_cada_hecho_de_riesgo_alto_lleva_el_minimo_al_nivel_mas_alto():
    snap = unit_with_mcp()
    escritura = copy.deepcopy(snap.governance)
    escritura["mcp"][SERVER]["write_operations"] = True
    casos = {
        "el servidor escribe fuera del cliente": snapshot(governance=escritura, mcp=snap.mcp),
        "hay credenciales declaradas": snap,
        "el dato es confidencial": snapshot(governance=with_governance(data_classification="confidential")),
        "el dato es restringido": snapshot(governance=with_governance(data_classification="restricted")),
    }
    for motivo, instantanea in casos.items():
        assert minimum_risk(instantanea) is RiskLevel.HIGH, motivo


def test_declarar_un_riesgo_por_debajo_del_calculado_es_error():
    # El nivel decide quién más aprueba: declarar de menos salta aprobadores obligatorios.
    snap = unit_with_mcp()
    governance = {**snap.governance, "risk_level": "low"}
    findings = check_declared_risk_is_not_lower(snapshot(governance=governance, mcp=snap.mcp))
    assert [f.rule for f in findings] == ["risk.declared-below-computed"]


def test_declarar_un_riesgo_por_encima_del_calculado_pasa():
    # Elevar es una decisión del autor; el campo existe sólo para eso.
    snap = snapshot(governance=with_governance(risk_level="high"))
    assert check_declared_risk_is_not_lower(snap) == ()


def test_no_declarar_riesgo_no_es_un_hallazgo():
    # El campo es opcional: si el cálculo ya da lo que corresponde, no hace falta ponerlo.
    assert check_declared_risk_is_not_lower(unit_with_mcp()) == ()
