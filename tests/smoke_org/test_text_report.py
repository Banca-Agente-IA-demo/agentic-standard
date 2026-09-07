"""El informe de texto sigue el formato de contracts/cli.md."""

from smoke_org.model import CheckResult, CheckStatus, Report
from smoke_org.text_report import render_line, render_text


def test_la_etiqueta_va_entre_corchetes_y_es_una_de_tres():
    labels = {
        CheckStatus.PASSED: "[PASA]",
        CheckStatus.FAILED: "[FALLA]",
        CheckStatus.UNCHECKED: "[SIN DATOS]",
    }
    for status, label in labels.items():
        assert render_line(CheckResult("x", "y", status)).startswith(label), status


def test_un_fallo_muestra_esperado_y_encontrado_con_esas_palabras():
    line = render_line(CheckResult("variables.present", "mkt", CheckStatus.FAILED, expected="A=1", found="ausente"))
    assert "esperado A=1, encontrado ausente" in line


def test_el_resumen_cuenta_los_tres_estados_y_el_veredicto_cierra_el_informe():
    report = Report(
        "demo",
        "Org",
        (
            CheckResult("a", "s", CheckStatus.PASSED),
            CheckResult("b", "s", CheckStatus.FAILED, expected="1", found="2"),
            CheckResult("c", "s", CheckStatus.UNCHECKED, detail="no se pudo consultar: x"),
        ),
    )
    text = render_text(report)
    assert "Resumen: 1 superadas, 1 fallidas, 1 sin comprobar" in text
    assert text.splitlines()[-1] == "Veredicto: NO SE PUDO COMPROBAR"


def test_los_tres_textos_de_veredicto_del_contrato():
    def report_with(status):
        return Report("demo", "Org", (CheckResult("a", "s", status),))

    expected = {
        CheckStatus.PASSED: "Veredicto: PASA",
        CheckStatus.FAILED: "Veredicto: NO PASA",
        CheckStatus.UNCHECKED: "Veredicto: NO SE PUDO COMPROBAR",
    }
    for status, last_line in expected.items():
        assert render_text(report_with(status)).splitlines()[-1] == last_line, status
