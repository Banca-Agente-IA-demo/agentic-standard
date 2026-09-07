"""Qué unidades toca un conjunto de archivos cambiados.

Puro: recibe rutas y devuelve rutas. Quien pregunta a git y quien recorre el árbol son adaptadores.
Lo usan la automatización en el registro y el asistente de autoría en la máquina del autor, que es la
razón de que viva aquí y no en un guion del workflow: si fueran dos implementaciones, el autor y la
automatización acabarían viendo cosas distintas.
"""

from __future__ import annotations


def units_touched(changed_paths: tuple[str, ...], unit_roots: tuple[str, ...]) -> tuple[str, ...]:
    """Las unidades a las que pertenece alguno de los archivos cambiados.

    `changed_paths` y `unit_roots` van en rutas relativas a la raíz del repositorio, con barras
    normales. Un archivo que no cae en ninguna unidad no aporta nada; una unidad que ya no existe
    tampoco, porque no está entre las raíces.
    """
    touched = {
        owner
        for path in changed_paths
        if (owner := owning_unit(path, unit_roots)) is not None
    }
    return tuple(sorted(touched))


def owning_unit(path: str, unit_roots: tuple[str, ...]) -> str | None:
    """La unidad más cercana que contiene el archivo, o `None` si no cae en ninguna.

    Se elige la más cercana porque una unidad dentro de otra no debería existir, y cuando existe el
    archivo pertenece a la interior. Que estén anidadas ya lo señala la regla de layout.
    """
    candidates = [root for root in unit_roots if path == root or path.startswith(root + "/")]
    return max(candidates, key=len) if candidates else None
