"""Renderiza el informe a texto legible según contracts/cli.md."""

from __future__ import annotations

from smoke_org.model import CheckResult, CheckStatus, Report, Verdict, verdict_of

_STATUS_LABELS = {
    CheckStatus.PASSED: "[PASA]",
    CheckStatus.FAILED: "[FALLA]",
    CheckStatus.UNCHECKED: "[SIN DATOS]",
}
_VERDICT_LABELS = {
    Verdict.PASS: "PASA",
    Verdict.FAIL: "NO PASA",
    Verdict.UNCHECKED: "NO SE PUDO COMPROBAR",
}
_LABEL_WIDTH = 11
_CHECK_ID_WIDTH = 19
_SCOPE_WIDTH = 24


def _detail(result: CheckResult) -> str:
    if result.expected is not None:
        return f"esperado {result.expected}, encontrado {result.found}"
    return result.detail


def render_line(result: CheckResult) -> str:
    label = _STATUS_LABELS[result.status].ljust(_LABEL_WIDTH)
    return f"{label} {result.check_id.ljust(_CHECK_ID_WIDTH)} {result.scope.ljust(_SCOPE_WIDTH)} {_detail(result)}".rstrip()


def render_text(report: Report) -> str:
    lines = [f"Prueba de humo: entorno {report.environment_name}, organización {report.organization}", ""]
    lines.extend(render_line(result) for result in report.results)
    lines.append("")
    lines.append(
        "Resumen: "
        f"{report.count(CheckStatus.PASSED)} superadas, "
        f"{report.count(CheckStatus.FAILED)} fallidas, "
        f"{report.count(CheckStatus.UNCHECKED)} sin comprobar"
    )
    lines.append(f"Veredicto: {_VERDICT_LABELS[verdict_of(report)]}")
    return "\n".join(lines)
