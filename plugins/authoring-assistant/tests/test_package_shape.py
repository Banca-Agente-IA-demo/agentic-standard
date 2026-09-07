"""El paquete se importa sin instalar nada y no arrastra dependencias.

Es lo que sostiene la promesa al autor: los clientes clonan la carpeta del plugin y los scripts
funcionan. Si alguien añade una dependencia externa al paquete, el asistente deja de funcionar en la
máquina de quien lo instale y no se enterará hasta entonces.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PLUGIN_ROOT / "authoring_assistant"
LAYERS = ("domain", "application", "ports", "adapters")

# Lo que la biblioteca estándar ofrece y el asistente puede usar. Cualquier otra cosa sería una
# dependencia que el autor tendría que instalar, y el plugin no instala nada.
STANDARD_LIBRARY = frozenset(sys.stdlib_module_names)

# El dominio se prueba con datos, sin repositorio (T1): nada que hable con el exterior entra ahí.
FORBIDDEN_IN_DOMAIN = ("subprocess", "pathlib", "os", "shutil")


def _modules(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def _imported_roots(module: Path) -> set[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_el_paquete_se_importa_sin_instalar_nada():
    import authoring_assistant

    assert Path(authoring_assistant.__file__).parent == PACKAGE_ROOT


def test_cada_capa_del_diseño_existe_y_dice_de_que_se_hace_cargo():
    for layer in LAYERS:
        init = PACKAGE_ROOT / layer / "__init__.py"
        assert init.is_file(), layer
        assert ast.get_docstring(ast.parse(init.read_text(encoding="utf-8"))), layer


def test_el_paquete_solo_usa_la_biblioteca_estandar():
    # El autor no ejecuta pip para tener el asistente. La única instalación que ocurre alguna vez es
    # la del validador, en un entorno privado y al primer uso.
    for module in _modules(PACKAGE_ROOT):
        externas = {r for r in _imported_roots(module) if r not in STANDARD_LIBRARY and r != "authoring_assistant"}
        assert not externas, f"{module.relative_to(PLUGIN_ROOT)}: {sorted(externas)}"


def test_el_dominio_no_habla_con_el_exterior():
    for module in _modules(PACKAGE_ROOT / "domain"):
        prohibidas = _imported_roots(module) & set(FORBIDDEN_IN_DOMAIN)
        assert not prohibidas, f"{module.name}: {sorted(prohibidas)}"


def test_el_dominio_no_importa_las_otras_capas():
    # La flecha de la dependencia apunta siempre hacia adentro (G5).
    for module in _modules(PACKAGE_ROOT / "domain"):
        texto = module.read_text(encoding="utf-8")
        for layer in ("application", "ports", "adapters"):
            assert f"authoring_assistant.{layer}" not in texto, f"{module.name} importa {layer}"
