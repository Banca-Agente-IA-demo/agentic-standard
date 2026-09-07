"""Comando `rules`: aplica las reglas del estándar a una unidad, o a las que un cambio ha tocado.

Es el composition root: el único módulo que conoce a la vez el dominio y los adaptadores, y el único
que los cablea. No hay paquete `ports/` porque no hay polimorfismo ni doble de test que lo justifique
(la lectura de disco tiene una sola implementación y las reglas reciben la instantánea ya construida),
y G5 prohíbe el puerto especulativo.

Códigos de salida: 0 cumple, 1 no cumple, 2 no se pudo comprobar.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from agentic_validator.adapters.contract import check_against_contract
from agentic_validator.adapters.reading import read_unit
from agentic_validator.adapters.report import render_json, render_text
from agentic_validator.adapters.repository import changed_paths, unit_roots
from agentic_validator.domain.discovery import units_touched
from agentic_validator.domain.model import Report, RunReport, ValidatorError, Verdict
from agentic_validator.domain.rules import run_rules

log = logging.getLogger(__name__)

TEXT_FORMAT = "text"
JSON_FORMAT = "json"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rules",
        description="Comprueba que una unidad publicable cumple las reglas del estándar agéntico.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Carpeta de la unidad, o raíz del repositorio si se usa --changed-since.",
    )
    parser.add_argument(
        "--changed-since",
        default=None,
        metavar="REF",
        help=(
            "Comprueba sólo las unidades que el trabajo actual ha tocado respecto a esa referencia, "
            "por ejemplo origin/main. Sin este argumento se comprueba la unidad indicada."
        ),
    )
    parser.add_argument(
        "--repository",
        default=None,
        help="Repositorio que aloja la unidad. Por defecto se deduce del árbol.",
    )
    parser.add_argument(
        "--format",
        choices=(TEXT_FORMAT, JSON_FORMAT),
        default=TEXT_FORMAT,
        help="Formato del informe: texto para una persona, json para el asistente.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Activa logging DEBUG.")
    return parser.parse_args(argv)


def _configure_output_encoding() -> None:
    """La consola de Windows no siempre es UTF-8 y el informe lleva acentos."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    in_ci = os.getenv("CI") == "true"
    fmt = "%(levelname)-8s %(name)s: %(message)s" if in_ci else "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def review_unit(root: Path, repository: str | None = None) -> Report:
    """Lee una unidad, la pasa por el contrato y por las reglas, y agrega sus hallazgos."""
    snapshot = read_unit(root, repository)
    findings = check_against_contract(snapshot.governance) + run_rules(snapshot)
    return Report(unit=snapshot.name, findings=findings)


def review_changed_units(repository_root: Path, base: str, repository: str | None = None) -> RunReport:
    """Comprueba las unidades que el trabajo actual ha tocado respecto a `base`.

    Cuando no hay con qué comparar, por ejemplo en el primer push de una rama, se comprueban todas las
    unidades del repositorio: comprobar de más es molesto, pero callar es peligroso.
    """
    roots = unit_roots(repository_root)
    changed = changed_paths(repository_root, base)
    if changed.unavailable is not None:
        log.warning("no se pudo comparar con %s (%s); se comprueban todas las unidades", base, changed.unavailable)
        touched = roots
    else:
        touched = units_touched(changed.paths, roots)
    log.info("unidades a comprobar: %s", ", ".join(touched) or "ninguna")
    reports = tuple(review_unit(repository_root / unit, repository) for unit in touched)
    return RunReport(scope=f"{repository_root.name} ({len(touched)} unidades tocadas)", reports=reports)


def _run(args: argparse.Namespace) -> RunReport:
    if args.changed_since is None:
        report = review_unit(args.path, args.repository)
        return RunReport(scope=f"la unidad {report.unit}", reports=(report,))
    return review_changed_units(args.path, args.changed_since, args.repository)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_output_encoding()
    _configure_logging(args.verbose)
    try:
        run = _run(args)
    except ValidatorError as exc:
        log.error("%s", exc)
        run = RunReport(scope=str(args.path), unavailable=str(exc))
    render = render_json if args.format == JSON_FORMAT else render_text
    print(render(run))
    return run.verdict.exit_code


if __name__ == "__main__":
    sys.exit(main())
