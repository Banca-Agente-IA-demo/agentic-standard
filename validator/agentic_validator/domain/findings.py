"""Se hace cargo de expresar el resultado de una comprobación y el veredicto que se deriva de él.

Una regla no decide si algo se publica: emite hallazgos. Quién bloquea y qué código de salida sale de
un conjunto de hallazgos se resuelve aquí, en un solo sitio, para que ninguna regla lo interprete a su
manera.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    rule: str
    """Identificador estable de la regla; aparece en el informe y es contrato."""
    where: str
    """Ruta relativa dentro de la unidad, o el nombre de la unidad si es de toda ella."""
    message: str
    """Qué está mal y por qué importa, en una frase."""

    @property
    def blocks(self) -> bool:
        return self.severity is Severity.ERROR


def error(rule: str, where: str, message: str) -> Finding:
    return Finding(Severity.ERROR, rule, where, message)


def warning(rule: str, where: str, message: str) -> Finding:
    return Finding(Severity.WARNING, rule, where, message)


class Verdict(Enum):
    COMPLIANT = 0
    NOT_COMPLIANT = 1
    UNREADABLE = 2

    @property
    def exit_code(self) -> int:
        return self.value


@dataclass(frozen=True)
class Report:
    unit: str
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.blocks)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if not f.blocks)

    @property
    def verdict(self) -> Verdict:
        return Verdict.NOT_COMPLIANT if self.errors else Verdict.COMPLIANT


@dataclass(frozen=True)
class RunReport:
    """El resultado de una ejecución, que puede abarcar varias unidades.

    Una sola unidad es el caso de un elemento. `unavailable` es para cuando no se pudo llegar a
    comprobar nada, que no es lo mismo que comprobar y no encontrar hallazgos.
    """

    scope: str
    """Qué se comprobó: la unidad, o el repositorio cuando se descubrieron las unidades tocadas."""
    reports: tuple[Report, ...] = ()
    unavailable: str | None = None

    @property
    def verdict(self) -> Verdict:
        if self.unavailable is not None:
            return Verdict.UNREADABLE
        return Verdict.NOT_COMPLIANT if any(report.errors for report in self.reports) else Verdict.COMPLIANT

    @property
    def error_count(self) -> int:
        return sum(len(report.errors) for report in self.reports)

    @property
    def warning_count(self) -> int:
        return sum(len(report.warnings) for report in self.reports)
