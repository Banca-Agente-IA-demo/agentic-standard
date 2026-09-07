"""Las comprobaciones de la prueba de humo: funciones puras de lo observado y lo esperado a resultados.

Cada comprobación devuelve un resultado por ámbito. Si la pieza observada que necesita no está
disponible, devuelve UNCHECKED con la razón y no deduce nada (FR-011).
"""

from __future__ import annotations

from collections.abc import Callable

from smoke_org.model import (
    ACTIONS_INTEGRATION_ID,
    APP_SECRET_NAMES,
    APP_SLUG,
    DOMAIN_TOPIC,
    INDEX_CHANNEL_VARIABLE,
    MAIN_RULESET_NAME,
    REQUIRED_CONTEXTS,
    TAGS_RULESET_NAME,
    TOPIC_VARIABLE,
    CheckResult,
    CheckStatus,
    Environment,
    Observed,
    OrganizationSnapshot,
    Report,
    RepositorySelection,
    Ruleset,
    RulesetEnforcement,
    TeamRoster,
)

ORGANIZATION_SCOPE = "organización"

Check = Callable[[OrganizationSnapshot, Environment, TeamRoster], tuple[CheckResult, ...]]


def _unchecked(check_id: str, scope: str, observed: Observed) -> CheckResult:
    reason = observed.unavailable.reason if observed.unavailable else "sin datos"
    return CheckResult(check_id, scope, CheckStatus.UNCHECKED, detail=f"no se pudo consultar: {reason}")


def _passed(check_id: str, scope: str, detail: str = "") -> CheckResult:
    return CheckResult(check_id, scope, CheckStatus.PASSED, detail=detail)


def _failed(check_id: str, scope: str, expected: str, found: str) -> CheckResult:
    return CheckResult(check_id, scope, CheckStatus.FAILED, expected=expected, found=found)


def check_org_settings(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "org.settings"
    if snapshot.organization.value is None:
        return (_unchecked(check_id, ORGANIZATION_SCOPE, snapshot.organization),)
    found = snapshot.organization.value
    expected_pairs = (
        ("plan", env.plan, found.plan),
        ("default_repository_permission", env.default_repository_permission, found.default_repository_permission),
        ("members_can_create_repositories", str(env.members_can_create_repositories).lower(),
         str(found.members_can_create_repositories).lower()),
    )
    mismatches = [(field, exp, got) for field, exp, got in expected_pairs if exp != got]
    if not mismatches:
        detail = " ".join(f"{field}={exp}" for field, exp, _ in expected_pairs)
        return (_passed(check_id, ORGANIZATION_SCOPE, detail),)
    return tuple(
        _failed(check_id, ORGANIZATION_SCOPE, f"{field}={exp}", f"{field}={got}") for field, exp, got in mismatches
    )


def check_teams(snapshot: OrganizationSnapshot, _: Environment, roster: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "teams.exist"
    if snapshot.team_slugs.value is None:
        return (_unchecked(check_id, ORGANIZATION_SCOPE, snapshot.team_slugs),)
    existing = snapshot.team_slugs.value
    return tuple(
        _passed(check_id, slug) if slug in existing else _failed(check_id, slug, "equipo existe", "ausente")
        for slug in sorted(roster.slugs)
    )


def check_app_installed(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "app.installed"
    if snapshot.app_installations.value is None:
        return (_unchecked(check_id, ORGANIZATION_SCOPE, snapshot.app_installations),)
    matching = [i for i in snapshot.app_installations.value if i.app_slug == APP_SLUG]
    if not matching:
        return (_failed(check_id, ORGANIZATION_SCOPE, f"App {APP_SLUG} instalada", "ausente"),)
    installation = matching[0]
    if installation.repository_selection is RepositorySelection.ALL:
        return (_passed(check_id, ORGANIZATION_SCOPE, "cobertura: todos los repositorios"),)
    covered = installation.repositories or frozenset()
    missing = [r for r in env.repositories_with_secrets() if r not in covered]
    if not missing:
        return (_passed(check_id, ORGANIZATION_SCOPE, "cobertura: selección que incluye todos los esperados"),)
    return tuple(_failed(check_id, repo, "repositorio cubierto por la App", "fuera de la instalación") for repo in missing)


def check_secrets(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "secrets.present"
    results: list[CheckResult] = []
    for repo in env.repositories_with_secrets():
        observed = snapshot.secret_names_by_repository.get(repo, Observed.missing("repositorio no consultado"))
        if observed.value is None:
            results.append(_unchecked(check_id, repo, observed))
            continue
        missing = [name for name in APP_SECRET_NAMES if name not in observed.value]
        if missing:
            results.extend(_failed(check_id, repo, f"secreto {name}", "ausente") for name in missing)
        else:
            results.append(_passed(check_id, repo))
    return tuple(results)


def check_variables(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "variables.present"
    results: list[CheckResult] = []
    for marketplace in env.marketplaces:
        repo = marketplace.repository
        observed = snapshot.variables_by_repository.get(repo, Observed.missing("repositorio no consultado"))
        if observed.value is None:
            results.append(_unchecked(check_id, repo, observed))
            continue
        expected = {INDEX_CHANNEL_VARIABLE: marketplace.channel.value, TOPIC_VARIABLE: DOMAIN_TOPIC}
        mismatches = [
            (name, value, observed.value.get(name)) for name, value in expected.items() if observed.value.get(name) != value
        ]
        if not mismatches:
            results.append(_passed(check_id, repo))
            continue
        results.extend(
            _failed(check_id, repo, f"{name}={value}", f"{name}={got}" if got is not None else "ausente")
            for name, value, got in mismatches
        )
    return tuple(results)


def check_topic(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "topic.domains"
    if snapshot.repositories_with_topic.value is None:
        return (_unchecked(check_id, ORGANIZATION_SCOPE, snapshot.repositories_with_topic),)
    tagged = snapshot.repositories_with_topic.value
    results = [
        _passed(check_id, repo) if repo in tagged else _failed(check_id, repo, f"topic {DOMAIN_TOPIC}", "ausente")
        for repo in env.domain_repositories
    ]
    results.extend(
        _failed(check_id, repo, f"sin topic {DOMAIN_TOPIC} (no es dominio)", "lo lleva")
        for repo in sorted(tagged - set(env.domain_repositories))
    )
    return tuple(results)


def _active_ruleset(rulesets: tuple[Ruleset, ...], name: str) -> Ruleset | None:
    for ruleset in rulesets:
        if ruleset.name == name and ruleset.enforcement is RulesetEnforcement.ACTIVE:
            return ruleset
    return None


def check_rulesets_present(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "rulesets.present"
    results: list[CheckResult] = []
    for repo in env.domain_repositories:
        observed = snapshot.rulesets_by_repository.get(repo, Observed.missing("repositorio no consultado"))
        if observed.value is None:
            results.append(_unchecked(check_id, repo, observed))
            continue
        missing = [name for name in (MAIN_RULESET_NAME, TAGS_RULESET_NAME) if _active_ruleset(observed.value, name) is None]
        if missing:
            results.extend(_failed(check_id, repo, f"ruleset {name} activo", "ausente o no activo") for name in missing)
        else:
            results.append(_passed(check_id, repo))
    return tuple(results)


def check_rulesets_contexts(snapshot: OrganizationSnapshot, env: Environment, _: TeamRoster) -> tuple[CheckResult, ...]:
    check_id = "rulesets.contexts"
    expected = sorted(f"{c} ({ACTIONS_INTEGRATION_ID})" for c in REQUIRED_CONTEXTS)
    results: list[CheckResult] = []
    for repo in env.domain_repositories:
        observed = snapshot.rulesets_by_repository.get(repo, Observed.missing("repositorio no consultado"))
        if observed.value is None:
            results.append(_unchecked(check_id, repo, observed))
            continue
        main = _active_ruleset(observed.value, MAIN_RULESET_NAME)
        if main is None:
            results.append(_failed(check_id, repo, ", ".join(expected), f"sin ruleset {MAIN_RULESET_NAME} activo"))
            continue
        found = sorted(f"{c.context} ({c.integration_id})" for c in main.required_contexts)
        if found == expected:
            results.append(_passed(check_id, repo))
        else:
            results.append(_failed(check_id, repo, ", ".join(expected), ", ".join(found) or "ninguno"))
    return tuple(results)


CHECKS: tuple[Check, ...] = (
    check_org_settings,
    check_teams,
    check_app_installed,
    check_secrets,
    check_variables,
    check_topic,
    check_rulesets_present,
    check_rulesets_contexts,
)


def run_checks(snapshot: OrganizationSnapshot, env: Environment, roster: TeamRoster) -> Report:
    """Recorre todas las comprobaciones sin detenerse en la primera fallida (FR-009)."""
    results: list[CheckResult] = []
    for check in CHECKS:
        results.extend(check(snapshot, env, roster))
    return Report(environment_name=env.name, organization=env.organization, results=tuple(results))
