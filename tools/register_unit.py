"""Entry point que registra la unidad recién sembrada en el catálogo de Port.

QUÉ CIERRA. Con la ficha creada, la unidad pasa a existir en **estado Desarrollo**, que el modelo
define como «hay ficha y ningún release». Hasta este paso la rama existía y la unidad no.

DOS DESENLACES, Y SOLO UNO ES UNA AVERÍA:

- El nombre ya tiene ficha: sale con 3. No es un fallo del workflow, es una respuesta, y quien lo
  invoca la convierte en el motivo que se devuelve a la persona.
- No se pudo hablar con el catálogo: sale con 2.

Trazabilidad. Documento 04 §2 del entregable E2 y apartado 4.4 de `FLUJO-CREATE-UNIT.md`.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from port_catalog.artifact_entity import register_artifacts, unregister_artifacts
from port_catalog.client import PortClient
from port_catalog.errors import CatalogError, UnitAlreadyRegisteredError
from port_catalog.unit_entity import register_unit, unregister_unit
from unit_seed.errors import SeedError
from unit_seed.unit_layout import declared_artifacts, unit_dir
from unit_seed.unit_request import UnitRequest

log = logging.getLogger(__name__)

_EXIT_CANNOT_REGISTER = 2
_EXIT_NAME_TAKEN = 3


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Registra la unidad sembrada en el catálogo de Port.")
    ap.add_argument("--payload", required=True, type=Path,
                    help="Archivo JSON con el formulario ya normalizado.")
    ap.add_argument("--sha", required=True,
                    help="Commit de la rama sembrada. Es la clave de cruce con el repositorio.")
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
        request = UnitRequest.model_validate(
            json.loads(args.payload.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError, SeedError) as exc:
        # Decía «en el job de validación». Corregido al converger create-unit a un solo job: lo que
        # cruza la frontera es el step de creación, no un job aparte.
        # Aquí el payload ya la cruzó, así que un fallo ahora es un defecto nuestro y no del
        # formulario.
        log.error("el payload normalizado no se pudo releer", exc_info=exc)
        sys.exit(_EXIT_CANNOT_REGISTER)

    client = PortClient.from_environment()
    try:
        register_unit(
            client,
            name=request.name,
            form=request.unit_form.value,
            owner_team=request.owner_team,
            owner_contact=request.team_mailbox,
            risk_level=request.risk_level.value,
            repository=request.repository,
            path=unit_dir(request).as_posix(),
            sha=args.sha,
            mcp_servers=request.mcp_servers,
        )
    except UnitAlreadyRegisteredError as exc:
        log.info("%s", exc)
        print(str(exc))
        sys.exit(_EXIT_NAME_TAKEN)
    except CatalogError as exc:
        log.error("no se pudo registrar la unidad en el catálogo", exc_info=exc)
        sys.exit(_EXIT_CANNOT_REGISTER)

    try:
        register_artifacts(client, request.name, _artifacts_of(request))
    except CatalogError as exc:
        # La unidad quedó registrada y sus artefactos no, así que el catálogo mostraría una unidad
        # vacía. Se retira la ficha de la unidad para no dejar esa media verdad, y el workflow
        # retirará la rama por el mismo motivo.
        log.error("no se pudieron registrar los artefactos; se retira la ficha", exc_info=exc)
        unregister_artifacts(client, request.name,
                             tuple(name for _, name, _ in _artifacts_of(request)))
        unregister_unit(client, request.name)
        sys.exit(_EXIT_CANNOT_REGISTER)


def _artifacts_of(request: UnitRequest) -> tuple[tuple[str, str, str], ...]:
    """Los artefactos con archivo propio, en tríos de tipo, nombre y ruta DENTRO de la unidad.

    La ruta es relativa a la unidad y apunta al archivo, no a su carpeta: `skills/x/SKILL.md` y no
    `skills/x`. Es la misma forma para los tres tipos, y así no hay que recordar cuál de ellos era la
    excepción.
    """
    root = unit_dir(request)
    return tuple((artifact.kind.value, artifact.name,
                  artifact.path.relative_to(root).as_posix())
                 for artifact in declared_artifacts(request))


if __name__ == "__main__":
    main()
