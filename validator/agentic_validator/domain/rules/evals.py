"""Se hace cargo de la suite de evaluación: que exista para cada artefacto y que tenga forma útil.

Una suite es lo que separa Experimental de una promesa (02 §8.2), así que su forma se juzga aparte del
artefacto que evalúa: son dos formatos distintos, dos fuentes distintas y dos momentos distintos del
ciclo de vida.
"""

from __future__ import annotations

from agentic_validator.domain.findings import Finding, error, warning
from agentic_validator.domain.snapshot import UnitSnapshot
from agentic_validator.domain.standard import (
    DETERMINISTIC_ASSERT_TYPES,
    EVALS_DIR,
    MIN_EVAL_CASES,
    REQUIRED_EVAL_CATEGORIES,
)


def check_eval_suites(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """La suite no es obligatoria aquí, pero si la unidad la trae tiene que tener la forma exigida."""
    findings: list[Finding] = []
    for suite in snapshot.eval_suites:
        if suite.error:
            findings.append(error("evals.unreadable", suite.path, f"no se pudo interpretar: {suite.error}"))
            continue
        tests = (suite.content or {}).get("tests")
        if not isinstance(tests, list) or len(tests) < MIN_EVAL_CASES:
            findings.append(
                error("evals.too-few-cases", suite.path, f"la suite necesita al menos {MIN_EVAL_CASES} casos")
            )
            continue
        findings.extend(_check_suite_cases(suite.path, tests))
    return tuple(findings)


def _check_suite_cases(path: str, tests: list) -> list[Finding]:
    findings: list[Finding] = []
    categories: set[str] = set()
    for case in tests:
        metadata = case.get("metadata") if isinstance(case, dict) else None
        category = (metadata or {}).get("category") if isinstance(metadata, dict) else None
        description = (case.get("description") if isinstance(case, dict) else None) or "sin descripción"
        if category is None:
            findings.append(
                error("evals.case-without-category", path, f"el caso {description!r} no declara metadata.category")
            )
        else:
            categories.add(str(category))
        assertions = case.get("assert") if isinstance(case, dict) else None
        types = {a.get("type") for a in assertions} if isinstance(assertions, list) else set()
        if not types & DETERMINISTIC_ASSERT_TYPES:
            findings.append(
                error(
                    "evals.case-without-deterministic-assertion",
                    path,
                    f"el caso {description!r} sólo se sostiene en el juez; sin él no dice nada",
                )
            )
    missing = sorted(REQUIRED_EVAL_CATEGORIES - categories)
    if missing:
        findings.append(
            error("evals.missing-categories", path, f"la suite no cubre las categorías: {', '.join(missing)}")
        )
    return findings


def check_every_artifact_has_its_suite(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Skill, agente y prompt necesitan suite para publicar (02 §8.2).

    Avisa en vez de bloquear: estas reglas corren también en el push, cuando el autor todavía está
    trabajando y la suite puede no existir. El bloqueo es de la verificación de la solicitud de cambio.
    """
    if not snapshot.text_artifacts:
        return ()
    suite_paths = {suite.path for suite in snapshot.eval_suites}
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        name = artifact.expected_name
        expected = (f"{EVALS_DIR}/{name}/promptfooconfig.yaml", f"{EVALS_DIR}/promptfooconfig.yaml")
        if not any(path in suite_paths for path in expected):
            findings.append(
                warning(
                    "evals.suite-missing",
                    artifact.path,
                    f"no tiene suite en {expected[0]}; sin ella no se llega a Experimental",
                )
            )
    return tuple(findings)
