"""Las pruebas del plugin importan el paquete como lo hace el asistente en la máquina del autor.

Añaden la raíz del plugin a `sys.path`, que es exactamente lo que hace cada script de entrada. Así la
prueba ejercita la misma forma de importar que el autor, y no una que sólo funciona en desarrollo.
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
