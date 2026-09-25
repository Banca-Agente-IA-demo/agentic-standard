"""Cliente del catálogo de Port para los workflows del estándar.

Existe aparte de `unit_seed` porque son dos responsabilidades distintas: una siembra archivos en un
repositorio y la otra habla con un servicio externo. Comparten el flujo de creación y nada más.

| Módulo | Qué hace |
|---|---|
| `client` | El token y las peticiones. No sabe qué es una unidad |
| `unit_lookup` | Si el nombre de una unidad está libre |
| `action_run` | Escribe el resultado y el motivo en la ejecución de la acción |
| `errors` | La jerarquía de errores del catálogo |
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
