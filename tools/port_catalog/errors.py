"""Jerarquía de errores del cliente del catálogo de Port.

Por qué existe. X1 pide una base propia por dominio para poder capturar a distintos niveles sin caer
en `except Exception`. Esta es la del catálogo, distinta de la del sembrador: una cosa es que el
formulario no describa una unidad sembrable y otra que Port no conteste.

Trazabilidad. AGENTS.md X1 y P2.
"""

from __future__ import annotations

__all__ = ["CatalogError", "CredentialsMissingError", "CatalogUnavailableError", "RunExhaustedError",
           "UnitAlreadyRegisteredError"]


class CatalogError(Exception):
    """Base del dominio del catálogo. Captura todo lo nuestro sin capturar bugs."""


class CredentialsMissingError(CatalogError):
    """Falta alguna de las dos credenciales de Port en el entorno."""


class CatalogUnavailableError(CatalogError):
    """Port contestó algo que no se puede usar, o no contestó."""


class UnitAlreadyRegisteredError(CatalogError):
    """El nombre de la unidad ya tiene ficha en el catálogo.

    Es una respuesta y no una avería: la ficha se crea con una operación que falla si el
    identificador existe, en vez de con una que actualiza, porque actualizar convertiría un choque de
    nombres en el borrado silencioso de la ficha ajena.
    """


class RunExhaustedError(CatalogError):
    """La ejecución ya terminó y Port no admite cambios sobre ella.

    Medido el 24 de septiembre de 2026: Port devuelve 422 `run_exhausted`. Tiene consecuencia de
    diseño, no es un detalle: el motivo hay que escribirlo MIENTRAS la ejecución sigue viva, así que
    el job que informa corre dentro del workflow y antes de que termine.
    """
