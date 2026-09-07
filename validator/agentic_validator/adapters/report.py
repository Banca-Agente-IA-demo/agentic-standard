"""El informe de hallazgos, legible para una persona y estructurado para el asistente.

El formato estructurado existe porque la constitución (principio I) exige que el modelo lea un campo
y no interprete texto.
"""

from __future__ import annotations

import json

from agentic_validator.domain.model import Report, Severity

_LABELS = {Severity.ERROR: "[ERROR]", Severity.WARNING: "[AVISO]"}
_LABEL_WIDTH = 8
_RULE_WIDTH = 38


def render_text(report: Report) -> str:
    lines = [f"Reglas del estándar sobre la unidad {report.unit}", ""]
    lines.extend(
        f"{_LABELS[finding.severity].ljust(_LABEL_WIDTH)} {finding.rule.ljust(_RULE_WIDTH)} {finding.where}: {finding.message}"
        for finding in report.findings
    )
    if report.findings:
        lines.append("")
    lines.append(f"Resumen: {len(report.errors)} errores, {len(report.warnings)} avisos")
    lines.append("Veredicto: CUMPLE" if not report.errors else "Veredicto: NO CUMPLE")
    return "\n".join(lines)


def render_json(report: Report) -> str:
    payload = {
        "unit": report.unit,
        "verdict": report.verdict.name.lower(),
        "errors": len(report.errors),
        "warnings": len(report.warnings),
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
    return json.dumps(payload, indent=2, ensure_ascii=False)
