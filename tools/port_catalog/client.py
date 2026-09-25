"""Cliente mínimo de la API de Port: obtiene el token y hace peticiones.

Por qué las credenciales salen del ENTORNO y no de un argumento. Un secreto en la línea de órdenes
queda en el historial del shell y en el registro de la herramienta que lo invoca. En CI llegan como
variables desde los secretos de la organización; en local, exportadas a mano.

Qué cubre y qué no. Habla con Port y nada más: no sabe qué es una unidad ni qué es una ejecución.
Eso vive en `unit_lookup` y en `action_run`, que lo reciben ya construido.

Trazabilidad. AGENTS.md OO6 y P2. Medición del 24 de septiembre de 2026 para el `?version=v2`.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from port_catalog.errors import CatalogUnavailableError, CredentialsMissingError

__all__ = ["PortClient", "BASE_URL"]

log = logging.getLogger(__name__)

BASE_URL = "https://api.getport.io/v1"
# Tope de espera de cada llamada. El job entero tiene su propio `timeout-minutes`; esto evita que una
# sola petición se lo coma.
REQUEST_TIMEOUT_SECONDS = 30


class PortClient:
    """Mantiene el token entre llamadas, que es el estado que justifica que esto sea una clase.

    Sin él, cada consulta pediría un token nuevo: tres llamadas donde bastan dos.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None

    @classmethod
    def from_environment(cls) -> PortClient:
        """Las dos credenciales, tal como llegan de los secretos de la organización."""
        client_id = os.getenv("PORT_CLIENT_ID", "")
        client_secret = os.getenv("PORT_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            raise CredentialsMissingError(
                "faltan PORT_CLIENT_ID o PORT_CLIENT_SECRET en el entorno")
        return cls(client_id, client_secret)

    def get(self, path: str) -> dict:
        return self._request("GET", path)

    def patch(self, path: str, body: dict) -> dict:
        return self._request("PATCH", path, body)

    def exists(self, path: str) -> bool:
        """Si el recurso existe. Un 404 es una respuesta, no un fallo."""
        try:
            self.get(path)
        except CatalogUnavailableError as exc:
            if " -> 404:" in str(exc):
                return False
            raise
        return True

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        return _call(method, path, self._authorization(), body)

    def _authorization(self) -> str:
        if self._token is None:
            answer = _call("POST", "/auth/access_token", None,
                           {"clientId": self._client_id, "clientSecret": self._client_secret})
            self._token = answer["accessToken"]
        return self._token


def _call(method: str, path: str, token: str | None, body: dict | None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(BASE_URL + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # El cuerpo de Port explica el motivo con un código propio (`run_exhausted`,
        # `invalid_request`), así que se conserva: sin él solo quedaría el número de estado.
        detail = error.read().decode("utf-8", errors="replace")[:400]
        raise CatalogUnavailableError(
            "%s %s -> %d: %s" % (method, path, error.code, detail)) from error
    except urllib.error.URLError as error:
        raise CatalogUnavailableError("%s %s no llegó a Port: %s" % (method, path, error)) from error
