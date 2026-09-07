"""El informe lo lee una persona: la concordancia de número no es un detalle estético.

«1 unidades comprobadas» delata que nadie miró la salida, y quien la lee deja de fiarse del resto.
"""

from __future__ import annotations

from agentic_validator.adapters.report import NOTHING_TO_CHECK, render_json, render_text
from agentic_validator.domain.findings import Report, RunReport, Severity, Verdict, error, warning

import json


def _run(*reports: Report, scope: str = "agents-demo (1 unidad tocada)") -> RunReport:
    return RunReport(scope=scope, reports=reports)


def test_una_sola_unidad_se_dice_en_singular():
    # Medido en la primera ejecución real del registro: el resumen salía como «1 unidades comprobadas».
    texto = render_text(_run(Report(unit="uno", findings=())))
    assert "1 unidad comprobada" in texto


def test_varias_unidades_se_dicen_en_plural():
    texto = render_text(_run(Report(unit="uno", findings=()), Report(unit="dos", findings=())))
    assert "2 unidades comprobadas" in texto


def test_un_solo_error_y_un_solo_aviso_se_dicen_en_singular():
    informe = Report(unit="uno", findings=(error("r", "a", "m"), warning("r", "a", "m")))
    texto = render_text(_run(informe))
    assert "1 error," in texto and "1 aviso" in texto


def test_sin_unidades_tocadas_lo_dice_y_el_veredicto_es_cumple():
    run = RunReport(scope="agents-demo (ninguna unidad tocada)")
    texto = render_text(run)
    assert NOTHING_TO_CHECK in texto and run.verdict is Verdict.COMPLIANT


def test_cuando_no_se_pudo_comprobar_se_dice_y_no_se_finge_un_veredicto():
    run = RunReport(scope="algo", unavailable="la carpeta no existe")
    texto = render_text(run)
    assert "No se pudo comprobar: la carpeta no existe" in texto
    assert "NO SE PUDO COMPROBAR" in texto and run.verdict is Verdict.UNREADABLE


def test_una_unidad_sin_hallazgos_lo_dice_en_vez_de_dejar_un_hueco():
    assert "sin hallazgos" in render_text(_run(Report(unit="uno", findings=())))


def test_el_formato_estructurado_lleva_el_recuento_y_cada_unidad():
    informe = Report(unit="uno", findings=(error("regla", "archivo", "motivo"),))
    payload = json.loads(render_json(_run(informe)))
    assert payload["units_checked"] == 1 and payload["errors"] == 1
    assert payload["units"][0]["findings"][0]["severity"] == Severity.ERROR.value
