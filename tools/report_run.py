"""Entry point que devuelve a Port el resultado de la ejecución y su motivo legible.

POR QUÉ NO BASTA EL INFORME AUTOMÁTICO de Port. Dice «falló», no POR QUÉ: quien rellenó el formulario
ve un rojo y tiene que abrir Actions para enterarse de que el nombre estaba ocupado. Y hay una razón
propia de este diseño: el job de validación termina EN VERDE con `status=false`, así que el informe
automático diría SUCCESS, que es lo contrario de lo que pasó.

Trazabilidad. Apartado 6 de `FLUJO-CREATE-UNIT.md`. AGENTS.md E1, E3, P3, L4, L5 y L9.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from port_catalog.action_run import RunStatus, report_run
from port_catalog.client import PortClient
from port_catalog.errors import CatalogError, RunExhaustedError

log = logging.getLogger(__name__)

_EXIT_CANNOT_REPORT = 2


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Escribe el resultado y el motivo en la ejecución de Port.")
    ap.add_argument("--run-id", required=True,
                    help="El identificador de la ejecución, tal como lo envió Port.")
    ap.add_argument("--status", required=True, choices=[status.value for status in RunStatus])
    ap.add_argument("--summary", required=True,
                    help="El motivo, en una frase que la persona pueda leer.")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="Activa logging DEBUG (detalles internos de ejecución).")
    return ap.parse_args()


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    in_ci = os.getenv("CI") == "true"
    fmt = ("%(levelname)-8s %(name)s · %(message)s" if in_ci
           else "%(asctime)s %(levelname)-8s %(name)s · %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)


def main() -> None:
    args = _parse_args()
    _configure_logging(verbose=args.verbose)
    try:
        report_run(PortClient.from_environment(), args.run_id,
                   RunStatus(args.status), args.summary)
    except RunExhaustedError as exc:
        # No se trata como un fallo del workflow: lo que se perdió es el mensaje, no el trabajo. Pero
        # queda un aviso, porque significa que algo cerró la ejecución antes de tiempo.
        log.warning("%s", exc)
        return
    except CatalogError as exc:
        log.error("no se pudo informar a Port", exc_info=exc)
        sys.exit(_EXIT_CANNOT_REPORT)


if __name__ == "__main__":
    main()
