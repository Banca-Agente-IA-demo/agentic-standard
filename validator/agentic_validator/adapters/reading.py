"""De la carpeta de una unidad a su instantánea.

Lee una sola vez y no juzga: un archivo corrupto se convierte en un motivo dentro de la instantánea,
no en una excepción, para que las reglas puedan informar de él como un hallazgo más.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

from agentic_validator.adapters.frontmatter import parse as parse_frontmatter
from agentic_validator.domain.model import (
    EVALS_DIR,
    GOVERNANCE_FILE,
    HOOKS_FILE,
    MANIFEST_FILE,
    MCP_FILE,
    EvalSuite,
    TextArtifact,
    UnitNotFoundError,
    UnitSnapshot,
)

log = logging.getLogger(__name__)

SKILL_FILE = "SKILL.md"
AGENT_SUFFIX = ".agent.md"
PROMPT_SUFFIX = ".prompt.md"
EVAL_SUITE_FILE = "promptfooconfig.yaml"


@dataclass(frozen=True)
class _Parsed:
    data: dict | None = None
    error: str | None = None


def _read_text(path: Path) -> _Parsed:
    try:
        return _Parsed(data={"text": path.read_text(encoding="utf-8")})
    except (OSError, UnicodeDecodeError) as failure:
        return _Parsed(error=str(failure))


def _read_json(path: Path) -> _Parsed:
    if not path.is_file():
        return _Parsed()
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as failure:
        return _Parsed(error=f"JSON inválido: {failure}")
    except (OSError, UnicodeDecodeError) as failure:
        return _Parsed(error=str(failure))
    if not isinstance(parsed, dict):
        return _Parsed(error="el archivo debe contener un objeto JSON")
    return _Parsed(data=parsed)


def _read_yaml(path: Path) -> _Parsed:
    if not path.is_file():
        return _Parsed()
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as failure:
        return _Parsed(error=f"YAML inválido: {str(failure).splitlines()[0]}")
    except (OSError, UnicodeDecodeError) as failure:
        return _Parsed(error=str(failure))
    if not isinstance(parsed, dict):
        return _Parsed(error="el archivo debe contener un mapa")
    return _Parsed(data=parsed)


def _text_artifact(root: Path, path: Path, expected_name: str) -> TextArtifact:
    relative = path.relative_to(root).as_posix()
    content = _read_text(path)
    if content.error:
        return TextArtifact(path=relative, expected_name=expected_name, error=content.error)
    parsed = parse_frontmatter((content.data or {})["text"])
    return TextArtifact(path=relative, expected_name=expected_name, frontmatter=parsed.data, error=parsed.error)


def _skills(root: Path) -> tuple[TextArtifact, ...]:
    """Un skill es una carpeta cuyo nombre impone el nombre declarado."""
    found = [
        _text_artifact(root, directory / SKILL_FILE, directory.name)
        for directory in sorted((root / "skills").iterdir())
        if directory.is_dir() and (directory / SKILL_FILE).is_file()
    ] if (root / "skills").is_dir() else []
    # Una unidad individual de tipo skill lleva su archivo en la raíz (04 §4).
    if (root / SKILL_FILE).is_file():
        found.append(_text_artifact(root, root / SKILL_FILE, root.name))
    return tuple(found)


def _by_suffix(root: Path, directory: str, suffix: str) -> tuple[TextArtifact, ...]:
    base = root / directory
    if not base.is_dir():
        return ()
    return tuple(
        _text_artifact(root, path, path.name[: -len(suffix)])
        for path in sorted(base.iterdir())
        if path.is_file() and path.name.endswith(suffix)
    )


def _eval_suites(root: Path) -> tuple[EvalSuite, ...]:
    base = root / EVALS_DIR
    if not base.is_dir():
        return ()
    paths = sorted(base.rglob(EVAL_SUITE_FILE))
    suites: list[EvalSuite] = []
    for path in paths:
        parsed = _read_yaml(path)
        suites.append(EvalSuite(path=path.relative_to(root).as_posix(), content=parsed.data, error=parsed.error))
    return tuple(suites)


def read_unit(root: Path, repository: str | None = None) -> UnitSnapshot:
    """Construye la instantánea. El repositorio se deduce del árbol si no se indica."""
    if not root.is_dir():
        raise UnitNotFoundError(f"{root} no es una carpeta")
    governance = _read_json(root / GOVERNANCE_FILE)
    manifest = _read_json(root / MANIFEST_FILE)
    mcp = _read_json(root / MCP_FILE)
    hooks = _read_json(root / HOOKS_FILE)
    log.debug("unidad %s: gobierno=%s manifiesto=%s", root.name, governance.data is not None, manifest.data is not None)
    return UnitSnapshot(
        name=root.name,
        repository=repository or _guess_repository(root),
        governance=governance.data,
        governance_error=governance.error,
        manifest=manifest.data,
        manifest_error=manifest.error,
        skills=_skills(root),
        agents=_by_suffix(root, "agents", AGENT_SUFFIX),
        prompts=_by_suffix(root, "commands", PROMPT_SUFFIX),
        mcp=mcp.data,
        mcp_error=mcp.error,
        hooks=hooks.data,
        hooks_error=hooks.error,
        eval_suites=_eval_suites(root),
    )


def _guess_repository(root: Path) -> str:
    """Una unidad vive en `<repositorio>/<tipo>/<unidad>`; el repositorio son dos niveles arriba."""
    parents = root.resolve().parents
    return parents[1].name if len(parents) > 1 else ""
