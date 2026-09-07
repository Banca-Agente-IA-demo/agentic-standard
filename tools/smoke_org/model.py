"""Dominio de la prueba de humo: nombres contrato, entorno esperado, lo observado y el veredicto.

Sin I/O: este módulo no importa subprocess, pathlib ni nada del proyecto fuera de sí mismo (T1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

# --- Nombres contrato del estándar (guía §2, §4, §7, §9; clarify 5 de la spec 001) -----------------
# Renombrar cualquiera de estos valores es una migración, no un refactor: los emparejan por texto los
# workflows, los rulesets y la guía de configuración.

APP_SLUG = "agentic-lifecycle"
APP_SECRET_NAMES = ("APP_ID", "APP_PRIVATE_KEY")
INDEX_CHANNEL_VARIABLE = "INDEX_CHANNEL"
TOPIC_VARIABLE = "AGENTIC_TOPIC"
MARKETPLACE_VARIABLE_NAMES = (INDEX_CHANNEL_VARIABLE, TOPIC_VARIABLE)
DOMAIN_TOPIC = "agentic-unit"
MAIN_RULESET_NAME = "protect-main"
TAGS_RULESET_NAME = "protect-tags"
REQUIRED_CONTEXTS = ("verify / rules", "verify / evals-verdict", "verify / collision")
ACTIONS_INTEGRATION_ID = 15368


class SmokeOrgError(Exception):
    """Excepción base de la herramienta."""


class EnvironmentFileError(SmokeOrgError):
    """El archivo de entorno o el mapa de equipos no se puede leer o no es válido."""


# --- Entorno esperado ------------------------------------------------------------------------------


class IndexChannel(str, Enum):
    PRODUCTION = "production"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class Marketplace:
    repository: str
    channel: IndexChannel


@dataclass(frozen=True)
class Environment:
    name: str
    organization: str
    plan: str
    default_repository_permission: str
    members_can_create_repositories: bool
    platform_repositories: tuple[str, ...]
    marketplaces: tuple[Marketplace, ...]
    domain_repositories: tuple[str, ...]

    def repositories_with_secrets(self) -> tuple[str, ...]:
        marketplace_repositories = tuple(m.repository for m in self.marketplaces)
        return self.platform_repositories + marketplace_repositories + self.domain_repositories


def validate_environment(environment: Environment) -> tuple[str, ...]:
    """Devuelve los problemas del entorno; vacío si es válido."""
    problems: list[str] = []
    if not environment.organization.strip():
        problems.append("organization no puede estar vacío")
    if not environment.marketplaces:
        problems.append("hace falta al menos un marketplace")
    channels = [m.channel for m in environment.marketplaces]
    if len(channels) != len(set(channels)):
        problems.append("dos marketplaces declaran el mismo canal")
    all_repositories = environment.repositories_with_secrets()
    if len(all_repositories) != len(set(all_repositories)):
        problems.append("un repositorio aparece en más de una lista")
    return tuple(problems)


@dataclass(frozen=True)
class TeamRoster:
    """Slugs de equipo que el mapa de papeles del estándar exige."""

    slugs: frozenset[str]


# --- Lo observado en GitHub -----------------------------------------------------------------------

T = TypeVar("T")


@dataclass(frozen=True)
class Unavailable:
    """La consulta no pudo hacerse; la razón es el mensaje de gh."""

    reason: str


@dataclass(frozen=True)
class Observed(Generic[T]):
    """Un valor observado o la razón por la que no se pudo observar."""

    value: T | None = None
    unavailable: Unavailable | None = None

    @classmethod
    def of(cls, value: T) -> "Observed[T]":
        return cls(value=value)

    @classmethod
    def missing(cls, reason: str) -> "Observed[T]":
        return cls(unavailable=Unavailable(reason))


@dataclass(frozen=True)
class OrganizationSettings:
    plan: str
    default_repository_permission: str
    members_can_create_repositories: bool


class RepositorySelection(str, Enum):
    ALL = "all"
    SELECTED = "selected"


@dataclass(frozen=True)
class AppInstallation:
    app_slug: str
    repository_selection: RepositorySelection
    repositories: frozenset[str] | None


class RulesetEnforcement(str, Enum):
    ACTIVE = "active"
    EVALUATE = "evaluate"
    DISABLED = "disabled"


class RulesetTarget(str, Enum):
    BRANCH = "branch"
    TAG = "tag"
    PUSH = "push"


@dataclass(frozen=True)
class RequiredContext:
    context: str
    integration_id: int | None


@dataclass(frozen=True)
class Ruleset:
    name: str
    enforcement: RulesetEnforcement
    target: RulesetTarget
    required_contexts: tuple[RequiredContext, ...]


@dataclass(frozen=True)
class OrganizationSnapshot:
    organization: Observed[OrganizationSettings]
    team_slugs: Observed[frozenset[str]]
    app_installations: Observed[tuple[AppInstallation, ...]]
    secret_names_by_repository: dict[str, Observed[frozenset[str]]]
    variables_by_repository: dict[str, Observed[dict[str, str]]]
    repositories_with_topic: Observed[frozenset[str]]
    rulesets_by_repository: dict[str, Observed[tuple[Ruleset, ...]]]


# --- Resultados y veredicto -----------------------------------------------------------------------


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNCHECKED = "unchecked"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    scope: str
    status: CheckStatus
    detail: str = ""
    expected: str | None = None
    found: str | None = None


@dataclass(frozen=True)
class Report:
    environment_name: str
    organization: str
    results: tuple[CheckResult, ...]

    def count(self, status: CheckStatus) -> int:
        return sum(1 for r in self.results if r.status is status)


class Verdict(Enum):
    PASS = 0
    FAIL = 1
    UNCHECKED = 2

    @property
    def exit_code(self) -> int:
        return self.value


def verdict_of(report: Report) -> Verdict:
    """UNCHECKED prevalece sobre FAIL: un informe incompleto no puede decir «no pasa» con certeza."""
    if report.count(CheckStatus.UNCHECKED):
        return Verdict.UNCHECKED
    if report.count(CheckStatus.FAILED):
        return Verdict.FAIL
    return Verdict.PASS
