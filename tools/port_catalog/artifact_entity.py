"""Registra en el catálogo una ficha por cada artefacto de la unidad.

POR QUÉ HACEN FALTA, si la unidad ya tiene la suya. Lo que se gobierna es la unidad, pero **lo que
alguien busca suele ser un artefacto**: «dónde están todos los servidores MCP», «qué hooks hay
instalados en la organización». Con una sola ficha por unidad esa pregunta no se puede hacer.

POR QUÉ SE CREAN AL SEMBRAR Y NO AL PUBLICAR. Es el mismo argumento por el que la unicidad del nombre
se pregunta a Port y no al índice del marketplace: **lo que solo aparece al publicar deja ciego al
catálogo durante todo el Desarrollo**. Y los cuatro datos de la ficha salen del árbol, que en este
punto ya existe.

`has_evals` NACE EN FALSO, y es deliberado. El esqueleto siembra el archivo de la suite, pero lleno
de marcadores: un archivo de `<<HAPPY_PATH_CASE>>` no es una suite, y decir que la tiene sería la
misma clase de mentira que una descripción plausible en un artefacto sin terminar. Lo pone en cierto
quien compruebe que la suite tiene casos de verdad.

EL ESTADO NO SE ESCRIBE AQUÍ: la ficha de artefacto no tiene estado propio, lo espeja de su unidad a
través de la relación. Una sola fuente para cada dato.

Trazabilidad. Documento 05 §3.1 y §3.3 del entregable E2, y el blueprint `agentic_artifact`.
"""

from __future__ import annotations

import logging

from port_catalog.client import PortClient
from port_catalog.errors import CatalogUnavailableError

__all__ = ["ARTIFACT_BLUEPRINT", "artifact_identifier", "register_artifacts", "unregister_artifacts"]

log = logging.getLogger(__name__)

# El blueprint de cada pieza de dentro de una unidad. Clave ya persistida en Port.
ARTIFACT_BLUEPRINT = "agentic_artifact"

# Separa la unidad del artefacto en el identificador. Es doble a propósito: un nombre de artefacto
# puede contener guiones simples, y con uno solo `a-b--c` y `a--b-c` serían el mismo texto.
_SEPARATOR = "--"


def artifact_identifier(unit_name: str, artifact_name: str) -> str:
    """El identificador de la ficha, que cualifica el artefacto con su unidad.

    Dos unidades pueden contener un artefacto con el mismo nombre, así que el nombre suelto no basta
    como identidad en el catálogo.
    """
    return unit_name + _SEPARATOR + artifact_name


def register_artifacts(client: PortClient, unit_name: str,
                       artifacts: tuple[tuple[str, str, str], ...]) -> None:
    """Crea una ficha por artefacto, en tríos de tipo, nombre y ruta dentro de la unidad.

    Se crean con `upsert`, al revés que la ficha de unidad: aquí el identificador ya está cualificado
    por la unidad, cuyo nombre acaba de comprobarse único, así que no hay ficha ajena que pisar. Lo
    que sí puede haber es un reintento del mismo registro, y fallar por eso sería ruido.
    """
    for kind, name, path in artifacts:
        client.post("/blueprints/%s/entities?upsert=true" % ARTIFACT_BLUEPRINT, {
            "identifier": artifact_identifier(unit_name, name),
            "title": name,
            "properties": {"type": kind, "path": path, "has_evals": False},
            "relations": {"unit": unit_name},
        })
    log.info("%d fichas de artefacto creadas para %s", len(artifacts), unit_name)


def unregister_artifacts(client: PortClient, unit_name: str,
                         artifact_names: tuple[str, ...]) -> None:
    """Retira las fichas de artefacto cuando la creación de la unidad no se pudo completar.

    Se retiran ANTES que la de la unidad: la relación va del artefacto a la unidad y es obligatoria,
    así que borrar la unidad primero dejaría fichas apuntando a algo que ya no existe.
    """
    for name in artifact_names:
        try:
            client.delete("/blueprints/%s/entities/%s"
                          % (ARTIFACT_BLUEPRINT, artifact_identifier(unit_name, name)))
        except CatalogUnavailableError as exc:
            # Que la compensación falle no puede tapar el fallo que la provocó.
            log.warning("no se pudo retirar la ficha del artefacto %s: %s", name, exc)
    log.info("fichas de artefacto de %s retiradas", unit_name)
