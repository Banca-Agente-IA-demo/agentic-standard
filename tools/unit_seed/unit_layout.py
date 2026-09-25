"""Dónde va cada cosa dentro de una unidad, y qué artefactos hay que sembrar.

Por qué existe. Es la convención de rutas del estándar, escrita una sola vez (C4). Antes estaba
repartida entre el sembrador y las dos plantillas de unidad, y la duda de si el manifiesto de la
forma individual era distinto del de la agrupada venía de ahí.

Qué cubre y qué no. Decide rutas y nombres. No lee ni escribe nada: recibe la petición y devuelve
posiciones, así que se prueba sin disco.

Trazabilidad. Documento 01 §2 y §3 del entregable E2. AGENTS.md C4, P7 y T3.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from unit_seed.errors import InvalidRequestError
from unit_seed.unit_kinds import ArtifactType, UnitForm
from unit_seed.unit_request import UnitRequest

__all__ = ["SeededArtifact", "unit_dir", "declared_artifacts", "manifest_path", "mcp_config_path",
           "hooks_path", "seeds_mcp_config", "seeds_hooks"]

# Dónde vive cada tipo DENTRO de la unidad, y con qué nombre de archivo. Los que no aparecen no son
# archivos con nombre propio: el servidor MCP y los hooks tienen cada uno su posición fija.
_ARTIFACT_LAYOUT = {
    ArtifactType.SKILL: ("skills", "%s/SKILL.md"),
    ArtifactType.AGENT: ("agents", "%s.agent.md"),
    ArtifactType.PROMPT: ("commands", "%s.prompt.md"),
}

# El directorio de primer nivel de una unidad individual, según su tipo. Es la otra mitad del árbol
# del documento 01: la agrupada siempre va bajo `plugins/`.
_INDIVIDUAL_ROOT = {
    ArtifactType.SKILL: "skills",
    ArtifactType.AGENT: "agents",
    ArtifactType.PROMPT: "commands",
    ArtifactType.HOOKS: "hooks",
    ArtifactType.MCP: "mcps",
}

_GROUPED_ROOT = "plugins"


@dataclass(frozen=True, slots=True)
class SeededArtifact:
    """Un artefacto a sembrar: su tipo, su nombre y dónde van su archivo y su suite.

    Viaja dentro del proceso y no se serializa, así que es una dataclass y no un modelo pydantic
    (C2). `slots=True` no es optimización: sin él, `artifact.evals_path = ...` con la errata crearía
    un atributo nuevo sin protestar y el valor real quedaría sin escribir.
    """

    kind: ArtifactType
    name: str
    path: PurePosixPath
    eval_path: PurePosixPath


def unit_dir(request: UnitRequest) -> PurePosixPath:
    """El directorio de la unidad dentro del repositorio de dominio."""
    if request.unit_form is UnitForm.GROUPED:
        return PurePosixPath(_GROUPED_ROOT) / request.name
    if request.artifact_type is None:
        raise InvalidRequestError("una unidad individual necesita el tipo de artefacto")
    return PurePosixPath(_INDIVIDUAL_ROOT[request.artifact_type]) / request.name


def manifest_path(request: UnitRequest) -> PurePosixPath:
    """El manifiesto va en el mismo sitio en las dos formas: es la afirmación del documento 01 §1."""
    return unit_dir(request) / ".claude-plugin" / "plugin.json"


def mcp_config_path(request: UnitRequest) -> PurePosixPath:
    """La raíz de la unidad, siempre.

    Fuera de ella los clientes NO descienden: un `.mcp.json` dentro de `skills/` no falla, no se lee.
    """
    return unit_dir(request) / ".mcp.json"


def hooks_path(request: UnitRequest) -> PurePosixPath:
    """Su subcarpeta, también en la forma individual: aplanarlo a la raíz no carga en Claude Code."""
    return unit_dir(request) / "hooks" / "hooks.json"


def declared_artifacts(request: UnitRequest) -> tuple[SeededArtifact, ...]:
    """Los artefactos con archivo propio que hay que sembrar.

    En la forma individual hay exactamente uno y **su nombre es el de la unidad**: no es una decisión
    del autor, es la identidad de la unidad, y de ahí sale la regla de que ese nombre aparece en
    cuatro sitios a la vez. El servidor MCP y los hooks no entran aquí: no son archivos con nombre
    propio, y sus posiciones las dan `mcp_config_path` y `hooks_path`.
    """
    if request.unit_form is UnitForm.INDIVIDUAL:
        if request.artifact_type is None:
            raise InvalidRequestError("una unidad individual necesita el tipo de artefacto")
        if request.artifact_type not in _ARTIFACT_LAYOUT:
            return ()
        return (_seeded(request, request.artifact_type, request.name),)
    # El orden es el del documento 01: skills, agentes y prompts. Se escriben los tres a la vista en
    # lugar de recorrer un mapa, porque cada tipo lee un campo distinto de la petición.
    return (
        tuple(_seeded(request, ArtifactType.SKILL, name) for name in request.skills)
        + tuple(_seeded(request, ArtifactType.AGENT, name) for name in request.agents)
        + tuple(_seeded(request, ArtifactType.PROMPT, name) for name in request.prompts)
    )


def seeds_mcp_config(request: UnitRequest) -> tuple[str, ...]:
    """Los nombres de servidor que llevará `.mcp.json`, vacío si la unidad no lleva ninguno."""
    if request.unit_form is UnitForm.INDIVIDUAL and request.artifact_type is ArtifactType.MCP:
        return (request.name,)
    return request.mcp_servers


def seeds_hooks(request: UnitRequest) -> bool:
    """Si la unidad llevará `hooks/hooks.json`."""
    return request.has_hooks or (request.unit_form is UnitForm.INDIVIDUAL
                                 and request.artifact_type is ArtifactType.HOOKS)


def _seeded(request: UnitRequest, kind: ArtifactType, name: str) -> SeededArtifact:
    folder, pattern = _ARTIFACT_LAYOUT[kind]
    root = unit_dir(request)
    # La unidad individual tiene un solo artefacto, así que su suite no necesita subcarpeta que la
    # distinga de ninguna otra.
    suite = ("evals" if request.unit_form is UnitForm.INDIVIDUAL else "evals/%s" % name)
    return SeededArtifact(
        kind=kind,
        name=name,
        path=root / folder / (pattern % name),
        eval_path=root / suite / "promptfooconfig.yaml",
    )
