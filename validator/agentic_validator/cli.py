"""Comando `rules`: aplica las reglas del estándar a la carpeta de una unidad publicable.

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
from agentic_validator.domain.model import Report, ValidatorError, Verdict
from agentic_validator.domain.rules import run_rules

log = logging.getLogger(__name__)

TEXT_FORMAT = "text"
JSON_FORMAT = "json"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rules",
        description="Comprueba que una unidad publicable cumple las reglas del estándar agéntico.",
    )
    parser.add_argument("unit", type=Path, help="Carpeta de la unidad, la que contiene GOVERNANCE.json.")
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
    """El caso de uso: lee la unidad, la pasa por el contrato y por las reglas, y agrega."""
    snapshot = read_unit(root, repository)
    findings = check_against_contract(snapshot.governance) + run_rules(snapshot)
    return Report(unit=snapshot.name, findings=findings)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_output_encoding()
    _configure_logging(args.verbose)
    try:
        report = review_unit(args.unit, args.repository)
    except ValidatorError as exc:
        log.error("%s", exc)
        return Verdict.UNREADABLE.exit_code
    render = render_json if args.format == JSON_FORMAT else render_text
    print(render(report))
    return report.verdict.exit_code


if __name__ == "__main__":
    sys.exit(main())
