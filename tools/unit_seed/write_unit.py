"""Escribe en disco el esqueleto de la unidad. Es el único módulo del paquete que toca el mundo.

Por qué existe aparte. Los tres módulos que deciden (`unit_request`, `unit_layout`, `unit_manifest`)
son puros y se prueban sin `tmp_path`. Todo el I/O se concentra aquí, así que el nombre del módulo y
el de su función pública declaran el efecto (S6).

Qué siembra, y qué deliberadamente no:

- El manifiesto con la identidad y el gobierno, desde `templates/unit/plugin.json`.
- Un archivo por artefacto declarado, con la descripción marcada como pendiente.
- Una suite de evals por artefacto con comportamiento, con los marcadores de la plantilla intactos.
  No es relleno: un archivo lleno de `<<HAPPY_PATH_CASE>>` no pasa el gate ni puede confundirse con
  una suite terminada, y el autor ve desde el primer commit cuántas le faltan.
- Un único `.mcp.json` y un único `hooks/hooks.json`, si se declararon.
- NINGUNA carpeta vacía: git no las versiona sin relleno, y una carpeta `agents/` vacía miente.

EL ESQUELETO NO PASA EL GATE, y es correcto. Una unidad en Desarrollo debe fallarlo: no tiene
descripciones reales ni casos de evals. Lo que no puede es PARECER terminada.

Trazabilidad. Documento 01 del entregable E2 y el apartado 3 de `DISENO-CREACION-DESDE-PORT.md`.
AGENTS.md S6, P2 y X1.
"""

from __future__ import annotations

import json
from pathlib import Path

from unit_seed.errors import TemplateNotFoundError
from unit_seed.unit_kinds import ArtifactType
from unit_seed.unit_layout import (declared_artifacts, hooks_path, manifest_path, mcp_config_path,
                                   seeds_hooks, seeds_mcp_config)
from unit_seed.unit_manifest import UNFINISHED_MARK, build_manifest, build_mcp_config
from unit_seed.unit_request import UnitRequest

__all__ = ["write_unit"]

_JSON_INDENT = 2

# El archivo de plantilla de cada tipo, bajo `templates/artifacts/<tipo>/`. Se escriben sus miembros
# y no se derivan del enumerado: un día alguien añade un tipo y este mapa no debe crecer solo (T3).
_ARTIFACT_TEMPLATE = {
    ArtifactType.SKILL: "SKILL.md",
    ArtifactType.AGENT: "NAME.agent.md",
    ArtifactType.PROMPT: "NAME.prompt.md",
}


def write_unit(request: UnitRequest, templates: Path, root: Path) -> tuple[Path, ...]:
    """Escribe la unidad bajo `root` y devuelve los archivos creados, en el orden en que se crearon."""
    written: list[Path] = [_write_manifest(request, templates, root)]
    written.extend(_write_artifacts(request, templates, root))
    written.extend(_write_mcp_config(request, root))
    written.extend(_write_hooks(request, templates, root))
    return tuple(written)


def _write_manifest(request: UnitRequest, templates: Path, root: Path) -> Path:
    """Una sola plantilla para las dos formas: lo que cambia entre ellas es el destino, no el texto."""
    template = json.loads(_read_template(templates / "unit" / "plugin.json"))
    return _write_json(root / manifest_path(request), build_manifest(request, template))


def _write_artifacts(request: UnitRequest, templates: Path, root: Path) -> list[Path]:
    eval_template = _read_template(templates / "artifacts" / "evals" / "promptfooconfig.yaml")
    written: list[Path] = []
    for artifact in declared_artifacts(request):
        body = _read_template(
            templates / "artifacts" / artifact.kind.value / _ARTIFACT_TEMPLATE[artifact.kind])
        written.append(_write_text(root / artifact.path, _fill(body, artifact.name)))
        written.append(_write_text(root / artifact.eval_path,
                                   eval_template.replace("<<NAME>>", artifact.name)))
    return written


def _write_mcp_config(request: UnitRequest, root: Path) -> list[Path]:
    servers = seeds_mcp_config(request)
    if not servers:
        return []
    return [_write_json(root / mcp_config_path(request), build_mcp_config(servers))]


def _write_hooks(request: UnitRequest, templates: Path, root: Path) -> list[Path]:
    if not seeds_hooks(request):
        return []
    template = _read_template(templates / "artifacts" / "hooks" / "hooks.json")
    return [_write_text(root / hooks_path(request), template)]


def _fill(template: str, name: str) -> str:
    """El cuerpo con el nombre puesto y la descripción marcada como pendiente.

    No depende del tipo: los tres formatos usan los mismos marcadores, y ramificar por el tipo sería
    ramificar por un dato que no cambia el resultado.
    """
    return (template
            .replace("<<NAME>>", name)
            .replace("<<DESCRIPTION>>", UNFINISHED_MARK)
            .replace("<<TITLE>>", name)
            .replace("<<TAGS>>", ""))


def _read_template(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as err:
        raise TemplateNotFoundError("no se pudo leer la plantilla %s: %s" % (path, err)) from err


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(path: Path, content: dict) -> Path:
    return _write_text(
        path, json.dumps(content, indent=_JSON_INDENT, ensure_ascii=False) + "\n")
