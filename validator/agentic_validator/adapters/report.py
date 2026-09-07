"""El informe de una ejecución, legible para una persona y estructurado para el asistente.

El formato estructurado existe porque la constitución (principio I) exige que el modelo lea un campo y
no interprete texto.
"""

from __future__ import annotations

import json

from agentic_validator.domain.model import Report, RunReport, Severity, Verdict

_LABELS = {Severity.ERROR: "[ERROR]", Severity.WARNING: "[AVISO]"}
_LABEL_WIDTH = 8
_RULE_WIDTH = 38
_VERDICT_LABELS = {
    Verdict.COMPLIANT: "CUMPLE",
    Verdict.NOT_COMPLIANT: "NO CUMPLE",
    Verdict.UNREADABLE: "NO SE PUDO COMPROBAR",
}
NOTHING_TO_CHECK = "Ninguna unidad tocada: no había nada que comprobar."


def _unit_lines(report: Report) -> list[str]:
    lines = [f"Unidad {report.unit}"]
    lines.extend(
        f"  {_LABELS[f.severity].ljust(_LABEL_WIDTH)} {f.rule.ljust(_RULE_WIDTH)} {f.where}: {f.message}"
        for f in report.findings
    )
    if not report.findings:
        lines.append("  sin hallazgos")
    return lines


def render_text(run: RunReport) -> str:
    lines = [f"Reglas del estándar sobre {run.scope}", ""]
    if run.unavailable is not None:
        lines.append(f"No se pudo comprobar: {run.unavailable}")
    elif not run.reports:
        lines.append(NOTHING_TO_CHECK)
    else:
        for report in run.reports:
            lines.extend(_unit_lines(report))
            lines.append("")
        lines.append(
            f"Resumen: {len(run.reports)} unidades comprobadas, "
            f"{run.error_count} errores, {run.warning_count} avisos"
        )
    lines.append(f"Veredicto: {_VERDICT_LABELS[run.verdict]}")
    return "\n".join(lines)


def render_json(run: RunReport) -> str:
    payload = {
        "scope": run.scope,
        "verdict": run.verdict.name.lower(),
        "unavailable": run.unavailable,
        "units_checked": len(run.reports),
        "errors": run.error_count,
        "warnings": run.warning_count,
        "units": [
            {
                "unit": report.unit,
                "verdict": report.verdict.name.lower(),
                "findings": [
                    {
                        "severity": finding.severity.value,
                        "rule": finding.rule,
                        "where": finding.where,
                        "message": finding.message,
                    }
                    for finding in report.findings
                ],
            }
            for report in run.reports
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
