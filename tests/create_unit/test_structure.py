"""La forma del paquete `create_unit`, comprobada sobre su código fuente.

Una regla de estructura sin prueba es una recomendación (PR2). Aquí se comprueban las tres que el
paquete no puede perder sin dejar de ser lo que el diseño describe: un archivo por paso con una sola
función exportada (E4), el efecto declarado en el nombre (S6), y ningún dato del dominio sin tipo
propio (C8).

Todas cuentan cuántos archivos recorrieron (PR3). El motivo lo dice el propio estándar y es la mejor
frase que tiene: **una regla verde y una muerta se ven igual**. Sin el recuento, un `rglob` que deja
de encontrar archivos pasa en verde sin mirar nada.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "tools" / "create_unit"
CLI = Path(__file__).resolve().parents[2] / "tools" / "create_unit_cli.py"

# Los pasos que el diseño fija. Se escriben sus miembros y no se derivan del recorrido: derivarlos
# haria que la prueba se adaptara sola a un paso borrado (T3).
EXPECTED_STEPS = (
    "read_port_payload",
    "read_team_slug",
    "read_catalog_units",
    "is_unit_name_free",
    "write_unit_skeleton",
    "compose_validation_status",
    "write_run_failure",
)
BANDS = ("input_sub_process", "pre_sub_process", "orchestration_sub_process", "output_sub_process")

# Los verbos que declaran el efecto. Un nombre que no empieza por uno de estos no dice si toca el
# mundo, que es lo que S6 exige.
EFFECT_PREFIXES = ("read_", "write_", "save_", "compose_", "verify_", "detect_",
                   "is_", "are_", "did_", "has_")

# Los tipos que C8 prohibe en una firma de datos del dominio. `Path` y los enumerados no entran
# porque declaran algo; estos no declaran nada.
FORBIDDEN_ANNOTATIONS = ("dict", "Dict", "Mapping", "MutableMapping", "object", "Any")

# La unica ventana que C8 admite: el valor entre `json.loads` y `model_validate`. Vive en dos pasos,
# y se nombran uno a uno para que abrir una tercera obligue a tocar esta lista.
C8_WINDOW_MODULES = ("read_port_payload.py", "read_catalog_units.py")


def _step_modules() -> list[Path]:
    return sorted(path for band in BANDS
                  for path in (PACKAGE / band / "steps").glob("*.py")
                  if path.name != "__init__.py")


def _all_modules() -> list[Path]:
    return sorted(path for path in PACKAGE.rglob("*.py") if path.name != "__init__.py")


def _exported_names(module: Path) -> list[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            return [element.value for element in node.value.elts  # type: ignore[attr-defined]
                    if isinstance(element, ast.Constant)]
    return []


def test_hay_exactamente_seis_pasos_y_son_los_que_el_diseno_fija() -> None:
    found = tuple(module.stem for module in _step_modules())
    assert sorted(found) == sorted(EXPECTED_STEPS), (
        "el paquete tiene %d pasos y el diseno fija %d. O falta alguno, o se anadio uno sin "
        "actualizar `CONVERGENCIA-CREATE-UNIT.md`. Encontrados: %s"
        % (len(found), len(EXPECTED_STEPS), ", ".join(sorted(found))))


def test_cada_paso_exporta_una_sola_funcion(name="E4") -> None:
    modules = _step_modules()
    assert modules, "el recorrido no encontro ningun paso: mira si la ruta del paquete cambio"
    for module in modules:
        exported = _exported_names(module)
        assert len(exported) == 1, (
            "%s exporta %d nombres (%s). Cada paso es su propio archivo con un `__all__` de un solo "
            "nombre: si hacen falta dos, son dos pasos (%s)"
            % (module.name, len(exported), ", ".join(exported) or "ninguno", name))


def test_el_nombre_de_cada_paso_declara_si_toca_el_mundo() -> None:
    modules = _step_modules()
    assert len(modules) == len(EXPECTED_STEPS), "el recorrido dejo de mirar donde tenia que mirar"
    for module in modules:
        exported = _exported_names(module)[0]
        assert exported.startswith(EFFECT_PREFIXES), (
            "%s exporta %r, que no empieza por ninguno de los verbos permitidos (%s). El nombre de "
            "un paso tiene que decir si lee, si escribe o si es un predicado (S6)"
            % (module.name, exported, ", ".join(EFFECT_PREFIXES)))


def test_ninguna_firma_del_paquete_declara_un_dato_sin_tipo_propio() -> None:
    modules = _all_modules() + [CLI]
    checked = 0
    offending: list[str] = []
    for module in modules:
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            checked += 1
            if module.name in C8_WINDOW_MODULES:
                continue
            for annotation in _annotations_of(node):
                if annotation in FORBIDDEN_ANNOTATIONS:
                    offending.append("%s::%s -> %s" % (module.name, node.name, annotation))
    assert checked >= len(EXPECTED_STEPS), (
        "solo se revisaron %d firmas y hay al menos %d pasos: el recorrido dejo de mirar"
        % (checked, len(EXPECTED_STEPS)))
    assert not offending, (
        "hay %d firmas con un dato sin tipo propio: %s. Si el dato tiene campos, declara su tipo en "
        "`commons/models/`; la unica ventana admitida es la linea entre `json.loads` y "
        "`model_validate` (C8)" % (len(offending), "; ".join(offending)))


def _annotations_of(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Los nombres de tipo que la firma menciona, incluidos los de dentro de un `tuple[...]`."""
    pieces: list[ast.expr] = [argument.annotation for argument in node.args.args
                              if argument.annotation is not None]
    pieces.extend(argument.annotation for argument in node.args.kwonlyargs
                  if argument.annotation is not None)
    if node.returns is not None:
        pieces.append(node.returns)
    names: list[str] = []
    for piece in pieces:
        for inner in ast.walk(piece):
            if isinstance(inner, ast.Name):
                names.append(inner.id)
            elif isinstance(inner, ast.Attribute):
                names.append(inner.attr)
            elif isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                names.append(inner.value)
    return names


def test_ningun_compositor_ramifica_sobre_el_contenido_de_un_sello() -> None:
    """E3: si un compositor tiene un `if`, ese `if` pertenece a un paso."""
    composers = [PACKAGE / "create_unit.py"]
    composers.extend(PACKAGE / band / ("%s.py" % band) for band in BANDS)
    assert len(composers) == len(BANDS) + 1, "falta algun compositor en el recorrido"
    for composer in composers:
        tree = ast.parse(composer.read_text(encoding="utf-8"))
        # El `if TYPE_CHECKING:` no cuenta y no es una excepcion cómoda: I2 lo EXIGE para lo que
        # solo se usa al tipar, y no ramifica sobre ningun dato, ramifica sobre el verificador.
        branches = [node for node in ast.walk(tree)
                    if isinstance(node, ast.IfExp)
                    or (isinstance(node, ast.If) and not _is_type_checking_guard(node))]
        assert not branches, (
            "%s ramifica en %d sitios. Un compositor solo dice en que orden se llama a que; la "
            "decision pertenece al paso (E3)" % (composer.name, len(branches)))


def _is_type_checking_guard(node: ast.If) -> bool:
    return isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"


def test_ningun_modulo_del_paquete_cruza_el_umbral_de_revision_en_silencio() -> None:
    """E6 usa ~300 lineas como aviso. Cruzarlo exige dividir o justificar, nunca callar."""
    threshold = 300
    modules = _all_modules()
    assert modules, "el recorrido no encontro ningun modulo"
    for module in modules:
        lines = len(module.read_text(encoding="utf-8").splitlines())
        assert lines <= threshold, (
            "%s tiene %d lineas. O se divide, o se deja un comentario al inicio justificando por que "
            "la cohesion real lo amerita (E6)" % (module.name, lines))
