"""Carga del archivo de entorno esperado y del mapa de papeles a equipos."""

from __future__ import annotations

import json
from pathlib import Path

from smoke_org.model import (
    Environment,
    EnvironmentFileError,
    IndexChannel,
    Marketplace,
    TeamRoster,
    validate_environment,
)

_ENVIRONMENT_KEYS = frozenset(
    {
        "organization",
        "plan",
        "default_repository_permission",
        "members_can_create_repositories",
        "platform_repositories",
        "marketplaces",
        "domain_repositories",
    }
)
_COMMENT_KEY = "$comment"


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EnvironmentFileError(f"no se pudo leer {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EnvironmentFileError(f"JSON inválido en {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EnvironmentFileError(f"{path} debe contener un objeto JSON")
    return data


def load_environment(path: Path) -> Environment:
    data = _read_json(path)
    unknown = set(data) - _ENVIRONMENT_KEYS - {_COMMENT_KEY}
    if unknown:
        raise EnvironmentFileError(f"claves desconocidas en {path}: {', '.join(sorted(unknown))}")
    missing = _ENVIRONMENT_KEYS - set(data)
    if missing:
        raise EnvironmentFileError(f"faltan claves en {path}: {', '.join(sorted(missing))}")
    try:
        environment = Environment(
            name=path.stem,
            organization=str(data["organization"]),
            plan=str(data["plan"]),
            default_repository_permission=str(data["default_repository_permission"]),
            members_can_create_repositories=bool(data["members_can_create_repositories"]),
            platform_repositories=tuple(data["platform_repositories"]),
            marketplaces=tuple(
                Marketplace(item["repository"], IndexChannel(item["channel"])) for item in data["marketplaces"]
            ),
            domain_repositories=tuple(data["domain_repositories"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EnvironmentFileError(f"estructura inválida en {path}: {exc}") from exc
    problems = validate_environment(environment)
    if problems:
        raise EnvironmentFileError(f"entorno {path.stem} inválido: {'; '.join(problems)}")
    return environment


def load_team_roster(path: Path) -> TeamRoster:
    """Recorre todos los papeles de config/teams.json: plataforma, control, piloto y cada dominio."""
    data = _read_json(path)
    slugs: set[str] = set()
    for key in ("platform_team", "pilot_team"):
        if data.get(key):
            slugs.add(str(data[key]))
    slugs.update(str(slug) for slug in data.get("control_functions", {}).values())
    for domain in data.get("domains", {}).values():
        for role in ("technical_lead", "champion"):
            if domain.get(role):
                slugs.add(str(domain[role]))
    if not slugs:
        raise EnvironmentFileError(f"{path} no declara ningún equipo")
    return TeamRoster(frozenset(slugs))
