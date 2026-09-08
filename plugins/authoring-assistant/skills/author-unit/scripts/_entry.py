"""Lo común a todos los puntos de entrada del asistente.

Cada script imprime **un solo documento estructurado** en la salida estándar y el diagnóstico en la de
error. Termina con éxito cuando ha podido clasificar, aunque el resultado sea de parada: detenerse es
un resultado, no un fallo. Sólo no poder ejecutar es un fallo.

Los prototipos del banco de pruebas no cumplían ninguna de las dos cosas, y se corrigió al portarlos.

Aquí también se añade la raíz del plugin al camino de búsqueda, que es cómo el núcleo llega al autor:
los clientes clonan la carpeta del plugin y no se instala nada.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

EXIT_CLASSIFIED = 0
EXIT_COULD_NOT_RUN = 2


def configure_streams() -> None:
    """La consola de Windows no siempre es UTF-8 y los mensajes llevan acentos."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def emit(payload: dict) -> int:
    """El documento a la salida estándar, y el éxito que corresponde a haber clasificado."""
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return EXIT_CLASSIFIED


def fail(reason: str) -> int:
    """No se pudo ejecutar. El diagnóstico va a la salida de error, no al documento."""
    print(f"{reason}", file=sys.stderr)
    print(json.dumps({"state": "unavailable", "message": reason}, ensure_ascii=False, indent=2))
    return EXIT_COULD_NOT_RUN


def without_nulls(payload: dict) -> dict:
    """Quita los campos vacíos: el modelo lee campos, y un campo nulo invita a interpretarlo."""
    return {key: value for key, value in payload.items() if value not in (None, (), [])}
