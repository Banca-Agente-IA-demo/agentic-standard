"""Adaptador de la línea de órdenes del paso de creación. Traduce argumentos a una llamada.

Por qué está fuera del paquete. E1: el adaptador no forma parte de la superficie importable. Aquí
solo hay parseo de argumentos, configuración de logging, el cableado y la traducción del veredicto a
JSON; toda la lógica vive en `create_unit/`.

Por qué la entrada es un ARCHIVO de JSON y no una lista de banderas. La acción de Port envía el
formulario entero en un único input con la forma `{{ .inputs | tojson }}`. Y es un archivo y no una
cadena porque el escapado de un JSON con comillas y saltos de línea no se comporta igual en `bash`
que en PowerShell, y un escapado que falla no da error: da OTRO JSON.

NO FALLA CUANDO EL FORMULARIO VIENE MAL, y es deliberado. Emite el veredicto y termina en verde, de
modo que el step que devuelve el motivo pueda correr sobre un job que no falló. Distingue «el
formulario venía mal» de «el workflow se rompió», que no son lo mismo para quien lo lee. Solo sale
con código distinto de cero cuando NO PUDO comprobar: sin credenciales, con Port sin contestar, sin
poder leer el archivo o sin poder escribir el esqueleto.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartados 3 y 4. AGENTS.md E1, E3, P3, L4, L5 y L9.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import sys
from pathlib import Path

from create_unit.commons.enums.validation_status import ValidationStatus
from create_unit.commons.models.seams import CreationOutcome
from create_unit.create_unit import create_unit
from port_catalog.client import PortClient
from port_catalog.errors import CatalogError
from unit_seed.errors import SeedError

log = logging.getLogger(__name__)

_EXIT_CANNOT_CHECK = 2

# Las plantillas viven en el mismo árbol que este adaptador, que es el del estándar. Se deriva de la
# posición del archivo y no se pide por bandera para que nadie pueda apuntar a unas plantillas de
# otra versión: la de las plantillas no puede separarse de la del código que las usa (C4).
DEFAULT_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Valida el formulario de Port y siembra el esqueleto de la unidad.")
    ap.add_argument("--payload", required=True, type=Path,
                    help="Archivo JSON con el formulario que envió Port.")
    ap.add_argument("--root", required=True, type=Path,
                    help="Raíz de trabajo donde se compone el esqueleto.")
    ap.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES,
                    help="Directorio templates/ del estándar. Por defecto, el de este árbol.")
    # Sin valor por defecto en el proceso (T4), pero opcional en la línea de órdenes: vacío significa
    # «esta invocación no viene del autoservicio», que es un caso legítimo y no una omisión.
    ap.add_argument("--run-id", default="",
                    help="Ejecucion de Port a la que devolver el motivo si el formulario no vale.")
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


def _path_from_environment(variable: str) -> Path | None:
    """El archivo que el runner expone en esa variable, o nada fuera de un runner."""
    value = os.getenv(variable)
    return Path(value) if value else None


def _write_github_outputs(outcome: CreationOutcome, destination: Path | None) -> None:
    """Emite el veredicto como outputs del step, una clave por línea.

    Cada clave va por separado y no como un JSON: un output de Actions es una cadena plana, y quien
    lo consume no debería tener que parsear nada para leer un estado. El motivo se aplana a una sola
    línea porque un output multilínea necesita delimitador y el texto viene de un formulario.
    """
    if destination is None:
        return
    lines = (f"validation_status={outcome.status.value}",
             f"reason={' '.join(outcome.reason.split())}",
             f"unit_name={outcome.unit_name}",
             f"normalized_payload={outcome.normalized_payload}")
    with destination.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_job_summary(outcome: CreationOutcome, destination: Path | None) -> None:
    """Escribe en el resumen del job lo que una persona necesita para saber qué pasó."""
    if destination is None:
        return
    if outcome.status is ValidationStatus.VALID:
        body = ["### Esqueleto compuesto", ""]
        body.extend("- `%s`" % path for path in outcome.files)
    else:
        body = ["### La unidad no se creo", "", outcome.reason]
    with destination.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(body) + "\n")


def main() -> None:
    args = _parse_args()
    _configure_logging(verbose=args.verbose)
    try:
        client = PortClient.from_environment()
        outcome = create_unit(args.payload, args.templates, args.root, client, args.run_id)
    except (OSError, json.JSONDecodeError) as exc:
        log.error("no se pudo leer el formulario ni escribir el esqueleto", exc_info=exc)
        sys.exit(_EXIT_CANNOT_CHECK)
    except CatalogError as exc:
        # No se pudo comprobar, que no es lo mismo que «está ocupado». Seguir como si estuviera libre
        # dejaría publicar una colisión; decir que está ocupado culparía al autor de un fallo nuestro.
        log.error("no se pudo consultar el catálogo: %s", exc)
        sys.exit(_EXIT_CANNOT_CHECK)
    except SeedError as exc:
        log.error("no se pudo sembrar el esqueleto: %s", exc)
        sys.exit(_EXIT_CANNOT_CHECK)
    _write_github_outputs(outcome, _path_from_environment("GITHUB_OUTPUT"))
    _write_job_summary(outcome, _path_from_environment("GITHUB_STEP_SUMMARY"))
    # El veredicto sale por stdout como un solo JSON y el diagnóstico por stderr: las dos corrientes
    # no se mezclan, así que llega limpio aunque el paso informe de cada archivo sembrado (L8).
    print(json.dumps(dataclasses.asdict(outcome), ensure_ascii=False))


if __name__ == "__main__":
    main()
