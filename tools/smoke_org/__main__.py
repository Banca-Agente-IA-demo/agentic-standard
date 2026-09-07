"""Entry point de smoke-org: parsea argumentos, cablea el lector de gh y traduce el veredicto a código.

Códigos de salida (contracts/cli.md): 0 pasa, 1 no pasa, 2 no se pudo comprobar. Los errores de uso
(entorno inexistente, JSON inválido, gh ausente) también terminan con 2.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from smoke_org.checks import run_checks
from smoke_org.files import load_environment, load_team_roster
from smoke_org.gh_reader import GhReader
from smoke_org.model import SmokeOrgError, Verdict, verdict_of
from smoke_org.text_report import render_text

log = logging.getLogger(__name__)

_DEFAULT_ENVIRONMENTS_DIR = Path(__file__).parent / "environments"
_DEFAULT_TEAMS_FILE = Path(__file__).resolve().parents[2] / "config" / "teams.json"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smoke-org",
        description="Comprueba que la organización de GitHub está configurada como exige el estándar.",
    )
    parser.add_argument("--env", required=True, help="Nombre del entorno: demo, bcp o <nombre>.json del directorio.")
    parser.add_argument(
        "--environments-dir",
        type=Path,
        default=_DEFAULT_ENVIRONMENTS_DIR,
        help="Directorio con los archivos de entorno (por defecto, el del paquete).",
    )
    parser.add_argument(
        "--teams-file",
        type=Path,
        default=_DEFAULT_TEAMS_FILE,
        help="Mapa de papeles a equipos (por defecto, config/teams.json del repositorio).",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Activa logging DEBUG (cada comando gh y su duración).")
    return parser.parse_args(argv)


def _configure_output_encoding() -> None:
    """La consola de Windows no siempre es UTF-8 y el informe lleva acentos (medido el 2026-09-07)."""
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_output_encoding()
    _configure_logging(args.verbose)
    try:
        environment = load_environment(args.environments_dir / f"{args.env}.json")
        roster = load_team_roster(args.teams_file)
    except SmokeOrgError as exc:
        log.error("%s", exc)
        return Verdict.UNCHECKED.exit_code
    log.info("Comprobando la organización %s con el entorno %s", environment.organization, environment.name)
    try:
        snapshot = GhReader(environment.organization).snapshot(environment)
    except FileNotFoundError:
        log.error("gh no está instalado o no está en el PATH")
        return Verdict.UNCHECKED.exit_code
    report = run_checks(snapshot, environment, roster)
    print(render_text(report))
    return verdict_of(report).exit_code


if __name__ == "__main__":
    sys.exit(main())
