"""Entry point del sembrador de unidades. Traduce argumentos a una llamada y no decide nada.

Por qué está fuera del paquete. E1: el adaptador de la línea de órdenes no forma parte de la
superficie importable. Aquí solo hay parseo de argumentos, configuración de logging y el cableado;
toda la lógica vive en `unit_seed/`.

Por qué la entrada es un ARCHIVO de JSON y no una lista de banderas. La acción de Port envía todo el
formulario en un único input, `payload`, con la forma `{{ .inputs | tojson }}`. Aceptar ese mismo
JSON evita una traducción a catorce banderas en el YAML del workflow, que sería lógica en shell sin
pruebas. Y es un archivo y no una cadena porque el workflow corre en runners de los dos sistemas y el
escapado de un JSON en la línea de órdenes no se comporta igual en `bash` que en PowerShell.

Trazabilidad. `create-unit-action.json` y el apartado 2 de `DISENO-CREACION-DESDE-PORT.md`.
AGENTS.md E1, E3, P3, L4, L5 y L9.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from unit_seed.errors import SeedError
from unit_seed.unit_request import UnitRequest
from unit_seed.write_unit import write_unit

log = logging.getLogger(__name__)

_EXIT_INVALID_REQUEST = 2
_EXIT_CANNOT_WRITE = 1


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Siembra el esqueleto de una unidad agéntica.")
    ap.add_argument("--payload", required=True, type=Path,
                    help="Archivo JSON con el formulario que envió Port.")
    ap.add_argument("--templates", required=True, type=Path,
                    help="Directorio templates/ del estándar.")
    ap.add_argument("--root", required=True, type=Path,
                    help="Raíz del repositorio de dominio donde se siembra la unidad.")
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
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        request = UnitRequest.model_validate(payload)
        written = write_unit(request, args.templates, args.root)
    except (json.JSONDecodeError, ValidationError, SeedError) as exc:
        log.error("no se pudo sembrar la unidad: %s", exc)
        sys.exit(_EXIT_INVALID_REQUEST)
    except OSError as exc:
        log.error("fallo al escribir la unidad", exc_info=exc)
        sys.exit(_EXIT_CANNOT_WRITE)
    for path in written:
        log.info("sembrado %s", path.relative_to(args.root))
    # La lista de archivos va a stdout porque la consume el workflow para el commit; el diagnóstico
    # de arriba va a stderr. Las dos corrientes no se mezclan (L8).
    print(json.dumps([str(path.relative_to(args.root).as_posix()) for path in written],
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
