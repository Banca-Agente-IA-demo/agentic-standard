"""El estándar se gobierna a sí mismo: sus propias unidades pasan las reglas que publica.

Es la prueba más barata de que el estándar sirve. Si publicar una unidad exige algo que la unidad del
propio equipo de plataforma no cumple, la exigencia es del papel y no del sistema.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_validator.cli import review_unit

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_NAME = "agentic-standard"
OWN_UNITS = sorted(p.parent for p in (REPO_ROOT / "plugins").rglob("GOVERNANCE.json"))

# Avisos que hoy son correctos y se espera que desaparezcan. Se enumeran para que, cuando dejen de
# salir, la prueba lo note y alguien borre la línea en vez de dejar el permiso abierto para siempre.
EXPECTED_WARNINGS = {
    "authoring-assistant": {"evals.suite-missing"},
}


@pytest.mark.parametrize("unit", OWN_UNITS, ids=lambda p: p.name)
def test_cada_unidad_del_estandar_cumple_sus_propias_reglas(unit: Path):
    report = review_unit(unit, REPOSITORY_NAME)
    assert report.errors == (), [f"{f.rule}: {f.where}: {f.message}" for f in report.errors]


@pytest.mark.parametrize("unit", OWN_UNITS, ids=lambda p: p.name)
def test_los_avisos_de_cada_unidad_son_los_que_se_esperan(unit: Path):
    # Un aviso nuevo que nadie mira acaba siendo ruido; uno que desaparece y nadie celebra deja la
    # excepción viva para siempre. Por eso se comparan los dos sentidos.
    report = review_unit(unit, REPOSITORY_NAME)
    assert {f.rule for f in report.warnings} == EXPECTED_WARNINGS.get(unit.name, set())


def test_el_estandar_tiene_al_menos_una_unidad_propia_que_gobernar():
    # Sin esto, las dos pruebas de arriba pasarían en vacío el día que alguien mueva las unidades.
    assert OWN_UNITS
