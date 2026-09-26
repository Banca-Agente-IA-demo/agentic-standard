"""El catálogo de unidades tal y como lo devuelve Port, y la lista de nombres que de ahí sale.

Por qué hay dos tipos y no uno. Son los dos lados de la frontera que traza C2: `CatalogUnitsAnswer`
es un modelo **pydantic** porque valida lo que contesta un servicio de fuera, y `CatalogUnits` es
una `dataclass` congelada porque a partir de ahí el dato solo viaja entre bandas de este proceso.

POR QUÉ SE LEE EL CATÁLOGO ENTERO Y NO SE PREGUNTA POR UNA ENTIDAD. El flujo anterior preguntaba si
existía la entidad con ese identificador, que responde la misma pregunta con una llamada más barata.
Se cambia a propósito: el diagrama de autoría pide **la lista en todos los estados**, y tenerla
permite añadir después la colisión por nombre de artefacto sin volver a hablar con Port. La lista
incluye las unidades en Desarrollo, que es justo lo que el índice del marketplace no puede ver.

Qué cubre y qué no. Declara la forma. No pregunta nada: quien llama es `read_catalog_units`.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md` apartado 4. AGENTS.md C2, C8 y P7.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

__all__ = ["CatalogEntity", "CatalogUnitsAnswer", "CatalogUnits"]


class CatalogEntity(BaseModel):
    """Una entidad del catálogo. Solo se declara el campo que alguien lee (C6).

    `extra="ignore"` no es dejadez: la respuesta de Port trae decenas de campos por entidad y
    declararlos todos ataría este código a un esquema que no gobernamos.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    identifier: str


class CatalogUnitsAnswer(BaseModel):
    """Lo que contesta `GET /blueprints/agentic_unit/entities`.

    Es la frontera exterior: aquí es donde el JSON de Port entra al sistema de tipos (C2).
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    entities: tuple[CatalogEntity, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogUnits:
    """Los nombres de unidad ya ocupados, en cualquier estado.

    `slots=True` no es optimización: sin él, `catalog.name = (...)` con la errata crearía un atributo
    nuevo sin protestar y la comprobación de unicidad miraría una tupla vacía (C2).
    """

    names: tuple[str, ...]
