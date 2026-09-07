"""Adaptador de lectura de GitHub a través de `gh` en un subproceso.

Usa la sesión que la persona ya tiene autenticada: la herramienta no lee credenciales (constitución
VI). El runner se inyecta para que las pruebas usen fixtures sin red (T4). Cualquier fallo de un
comando se traduce a Unavailable con el mensaje de gh; nunca a una excepción.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Protocol

from smoke_org.model import (
    DOMAIN_TOPIC,
    AppInstallation,
    Environment,
    Observed,
    OrganizationSettings,
    OrganizationSnapshot,
    RepositorySelection,
    RequiredContext,
    Ruleset,
    RulesetEnforcement,
    RulesetTarget,
)

log = logging.getLogger(__name__)

# Tope de repositorios que gh repo list devuelve en una llamada; cubre cualquier organización de BCP.
_REPO_LIST_LIMIT = 1000
_REQUIRED_STATUS_CHECKS_RULE = "required_status_checks"

def _propagate(observed: Observed[Any]) -> Observed[Any]:
    """Convierte un Observed sin valor en uno del tipo destino con la misma razón."""
    reason = observed.unavailable.reason if observed.unavailable else "sin datos"
    return Observed.missing(reason)


@dataclass(frozen=True)
class CommandOutput:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def __call__(self, command: list[str]) -> CommandOutput: ...


def run_subprocess(command: list[str]) -> CommandOutput:
    """Runner real: ejecuta gh y captura salida; no lanza por código distinto de cero."""
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    return CommandOutput(completed.returncode, completed.stdout, completed.stderr)


def _error_message(output: CommandOutput) -> str:
    """gh escribe el cuerpo JSON del error en stdout y un resumen en stderr (medido el 2026-09-07)."""
    try:
        body = json.loads(output.stdout) if output.stdout.strip() else {}
    except json.JSONDecodeError:
        body = {}
    if isinstance(body, dict) and body.get("message"):
        return f"gh: {body['message']} (HTTP {body.get('status', '?')})"
    lines = [line for line in output.stderr.strip().splitlines() if line.strip()]
    return lines[-1] if lines else f"gh terminó con código {output.returncode}"


class GhReader:
    """Lee la organización pieza a pieza; cada pieza es Observed."""

    def __init__(self, organization: str, runner: CommandRunner = run_subprocess) -> None:
        self._org = organization
        self._runner = runner

    def _query(self, command: list[str]) -> Observed[Any]:
        started = time.monotonic()
        output = self._runner(command)
        log.debug("%s -> código %s en %.2fs", " ".join(command), output.returncode, time.monotonic() - started)
        if output.returncode != 0:
            return Observed.missing(_error_message(output))
        try:
            return Observed.of(json.loads(output.stdout))
        except json.JSONDecodeError as exc:
            return Observed.missing(f"respuesta de gh no es JSON: {exc}")

    def _api(self, path: str, *extra: str) -> Observed[Any]:
        return self._query(["gh", "api", path, *extra])

    def organization(self) -> Observed[OrganizationSettings]:
        observed = self._api(f"orgs/{self._org}")
        if observed.value is None:
            return _propagate(observed)
        data = observed.value
        return Observed.of(
            OrganizationSettings(
                plan=str(data.get("plan", {}).get("name", "")),
                default_repository_permission=str(data.get("default_repository_permission", "")),
                members_can_create_repositories=bool(data.get("members_can_create_repositories", False)),
            )
        )

    def team_slugs(self) -> Observed[frozenset[str]]:
        observed = self._api(f"orgs/{self._org}/teams", "--paginate")
        if observed.value is None:
            return _propagate(observed)
        return Observed.of(frozenset(team["slug"] for team in observed.value))

    def app_installations(self) -> Observed[tuple[AppInstallation, ...]]:
        observed = self._api(f"orgs/{self._org}/installations")
        if observed.value is None:
            return _propagate(observed)
        installations = []
        for item in observed.value.get("installations", []):
            selection = RepositorySelection(item["repository_selection"])
            repositories = None
            if selection is RepositorySelection.SELECTED:
                repositories = self._installation_repositories(int(item["id"]))
            installations.append(AppInstallation(item["app_slug"], selection, repositories))
        return Observed.of(tuple(installations))

    def _installation_repositories(self, installation_id: int) -> frozenset[str] | None:
        observed = self._api(f"user/installations/{installation_id}/repositories", "--paginate")
        if observed.value is None:
            return None
        return frozenset(repo["name"] for repo in observed.value.get("repositories", []))

    def secret_names(self, repository: str) -> Observed[frozenset[str]]:
        observed = self._query(["gh", "secret", "list", "--repo", f"{self._org}/{repository}", "--json", "name"])
        if observed.value is None:
            return _propagate(observed)
        return Observed.of(frozenset(item["name"] for item in observed.value))

    def variables(self, repository: str) -> Observed[dict[str, str]]:
        observed = self._query(
            ["gh", "variable", "list", "--repo", f"{self._org}/{repository}", "--json", "name,value"]
        )
        if observed.value is None:
            return _propagate(observed)
        return Observed.of({item["name"]: item["value"] for item in observed.value})

    def repositories_with_topic(self, topic: str) -> Observed[frozenset[str]]:
        observed = self._query(
            ["gh", "repo", "list", self._org, "--topic", topic, "--json", "name", "--limit", str(_REPO_LIST_LIMIT)]
        )
        if observed.value is None:
            return _propagate(observed)
        return Observed.of(frozenset(item["name"] for item in observed.value))

    def rulesets(self, repository: str) -> Observed[tuple[Ruleset, ...]]:
        """La lista no trae las reglas: hay que pedir cada ruleset por id (medido el 2026-09-07)."""
        listed = self._api(f"repos/{self._org}/{repository}/rulesets")
        if listed.value is None:
            return _propagate(listed)
        rulesets = []
        for summary in listed.value:
            detail = self._api(f"repos/{self._org}/{repository}/rulesets/{summary['id']}")
            if detail.value is None:
                return _propagate(detail)
            rulesets.append(_parse_ruleset(detail.value))
        return Observed.of(tuple(rulesets))

    def snapshot(self, environment: Environment) -> OrganizationSnapshot:
        return OrganizationSnapshot(
            organization=self.organization(),
            team_slugs=self.team_slugs(),
            app_installations=self.app_installations(),
            secret_names_by_repository={r: self.secret_names(r) for r in environment.repositories_with_secrets()},
            variables_by_repository={m.repository: self.variables(m.repository) for m in environment.marketplaces},
            repositories_with_topic=self.repositories_with_topic(DOMAIN_TOPIC),
            rulesets_by_repository={r: self.rulesets(r) for r in environment.domain_repositories},
        )


def _parse_ruleset(data: dict[str, Any]) -> Ruleset:
    contexts: list[RequiredContext] = []
    for rule in data.get("rules", []):
        if rule.get("type") != _REQUIRED_STATUS_CHECKS_RULE:
            continue
        for item in rule.get("parameters", {}).get("required_status_checks", []):
            contexts.append(RequiredContext(item["context"], item.get("integration_id")))
    return Ruleset(
        name=data["name"],
        enforcement=RulesetEnforcement(data["enforcement"]),
        target=RulesetTarget(data["target"]),
        required_contexts=tuple(contexts),
    )
