"""Entry point del job de validación. Decide si el formulario describe una unidad que se puede sembrar.

COMPRUEBA DOS COSAS DISTINTAS, en este orden:

1. La FORMA del payload, con el mismo modelo que usa el sembrador. No se reimplementa aquí: si el
   workflow validara por su cuenta habría dos definiciones de «payload válido», y el día que
   divergieran el workflow diría que está bien y el sembrador reventaría a mitad, dejando una rama a
   medio escribir.
2. Que el NOMBRE esté libre en el catálogo, que solo se puede preguntar a Port.

NO FALLA CUANDO EL PAYLOAD ES INVÁLIDO, y es deliberado. Emite `status=false` y termina en verde, de
modo que el job que devuelve el motivo pueda arrancar sobre un job que no falló. Distingue «el
formulario venía mal» de «el workflow se rompió», que no son lo mismo para quien lo lee. Solo sale con
código distinto de cero cuando NO PUDO comprobar: sin credenciales, o con Port sin contestar.

Trazabilidad. Apartados 2 y 3 de `FLUJO-CREATE-UNIT.md`. AGENTS.md E1, E3, P3 y X2.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from port_catalog.client import PortClient
from port_catalog.errors import CatalogError
from port_catalog.team_lookup import resolve_team_slug
from port_catalog.unit_lookup import is_name_taken
from unit_seed.errors import SeedError
from unit_seed.unit_request import UnitRequest

log = logging.getLogger(__name__)

_EXIT_CANNOT_CHECK = 2


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Comprueba si el formulario de Port describe una unidad que se puede sembrar.")
    ap.add_argument("--payload", required=True, type=Path,
                    help="Archivo JSON con el formulario que envió Port.")
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


def _verdict(status: bool, reason: str, request: UnitRequest | None) -> dict:
    """El veredicto tiene siempre las mismas cuatro claves, valga lo que valga `status`.

    Un contrato que cambia de forma según el resultado obliga a quien lo lee a mirar primero el
    estado para saber qué campos existen.
    """
    return {
        "status": status,
        "reason": reason,
        "unit_name": request.name if request else "",
        "normalized_payload": request.model_dump(mode="json") if request else {},
    }


def main() -> None:
    args = _parse_args()
    _configure_logging(verbose=args.verbose)
    try:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("no se pudo leer el payload", exc_info=exc)
        sys.exit(_EXIT_CANNOT_CHECK)

    try:
        request = UnitRequest.model_validate(payload)
    except (ValidationError, SeedError) as exc:
        log.info("el formulario no describe una unidad sembrable: %s", exc)
        print(json.dumps(_verdict(False, _readable(exc), None), ensure_ascii=False))
        return

    try:
        client = PortClient.from_environment()
        # El formulario envía el id numérico del equipo de GitHub; el manifiesto necesita el slug.
        # Se traduce ANTES de la comprobación de nombre para que las dos consultas compartan token.
        request = request.model_copy(
            update={"owner_team": resolve_team_slug(client, request.owner_team)})
        taken = is_name_taken(client, request.name)
    except CatalogError as exc:
        # No se pudo comprobar, que no es lo mismo que «está ocupado». Seguir como si estuviera libre
        # dejaría publicar una colisión; decir que está ocupado culparía al autor de un fallo nuestro.
        log.error("no se pudo consultar el catálogo: %s", exc)
        sys.exit(_EXIT_CANNOT_CHECK)

    if taken:
        reason = ("El nombre %s ya esta ocupado por otra unidad del catalogo, en cualquier estado, "
                  "incluido Desarrollo. Elige otro." % request.name)
        log.info("%s", reason)
        print(json.dumps(_verdict(False, reason, request), ensure_ascii=False))
        return

    log.info("el formulario es valido y el nombre %s esta libre", request.name)
    print(json.dumps(_verdict(True, "", request), ensure_ascii=False))


def _readable(error: Exception) -> str:
    """El motivo, en una frase que la persona pueda leer en la pantalla de Port.

    El volcado de pydantic nombra el campo y el porqué, que es justo lo que hace falta; lo que sobra
    es el enlace a la documentación que añade al final de cada error.
    """
    return " ".join(str(error).split())[:500]


if __name__ == "__main__":
    main()
