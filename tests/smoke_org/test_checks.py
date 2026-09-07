"""Cada comprobación con datos: superada, fallida por cada defecto, y sin datos (T1, T5)."""

from smoke_org.checks import (
    CHECKS,
    check_app_installed,
    check_org_settings,
    check_rulesets_contexts,
    check_rulesets_present,
    check_secrets,
    check_teams,
    check_topic,
    check_variables,
    run_checks,
)
from smoke_org.model import (
    ACTIONS_INTEGRATION_ID,
    APP_SLUG,
    REQUIRED_CONTEXTS,
    AppInstallation,
    CheckStatus,
    Environment,
    IndexChannel,
    Marketplace,
    Observed,
    OrganizationSettings,
    OrganizationSnapshot,
    RepositorySelection,
    RequiredContext,
    Ruleset,
    RulesetEnforcement,
    RulesetTarget,
    TeamRoster,
)

ENV = Environment(
    name="demo",
    organization="Org",
    plan="free",
    default_repository_permission="read",
    members_can_create_repositories=False,
    platform_repositories=("standard",),
    marketplaces=(Marketplace("mkt", IndexChannel.PRODUCTION), Marketplace("mkt-exp", IndexChannel.EXPERIMENTAL)),
    domain_repositories=("agents-a",),
)
ROSTER = TeamRoster(frozenset({"platform-team", "lt-a"}))
CONTEXTS = tuple(RequiredContext(c, ACTIONS_INTEGRATION_ID) for c in REQUIRED_CONTEXTS)
MAIN = Ruleset("protect-main", RulesetEnforcement.ACTIVE, RulesetTarget.BRANCH, CONTEXTS)
TAGS = Ruleset("protect-tags", RulesetEnforcement.ACTIVE, RulesetTarget.TAG, ())
ALL_REPOS = ("standard", "mkt", "mkt-exp", "agents-a")


def _snapshot(**overrides) -> OrganizationSnapshot:
    base = dict(
        organization=Observed.of(OrganizationSettings("free", "read", False)),
        team_slugs=Observed.of(frozenset({"platform-team", "lt-a", "extra"})),
        app_installations=Observed.of((AppInstallation(APP_SLUG, RepositorySelection.ALL, None),)),
        secret_names_by_repository={r: Observed.of(frozenset({"APP_ID", "APP_PRIVATE_KEY"})) for r in ALL_REPOS},
        variables_by_repository={
            "mkt": Observed.of({"INDEX_CHANNEL": "production", "AGENTIC_TOPIC": "agentic-unit"}),
            "mkt-exp": Observed.of({"INDEX_CHANNEL": "experimental", "AGENTIC_TOPIC": "agentic-unit"}),
        },
        repositories_with_topic=Observed.of(frozenset({"agents-a"})),
        rulesets_by_repository={"agents-a": Observed.of((MAIN, TAGS))},
    )
    return OrganizationSnapshot(**{**base, **overrides})


def _statuses(results):
    return [r.status for r in results]


def _failures(results):
    return [r for r in results if r.status is CheckStatus.FAILED]


# --- organización ----------------------------------------------------------------------------------


def test_organizacion_configurada_como_el_entorno_pasa():
    assert _statuses(check_org_settings(_snapshot(), ENV, ROSTER)) == [CheckStatus.PASSED]


def test_cada_campo_distinto_de_la_organizacion_falla_nombrandolo():
    cases = (
        ("plan", OrganizationSettings("enterprise", "read", False)),
        ("default_repository_permission", OrganizationSettings("free", "none", False)),
        ("members_can_create_repositories", OrganizationSettings("free", "read", True)),
    )
    for field, settings in cases:
        failures = _failures(check_org_settings(_snapshot(organization=Observed.of(settings)), ENV, ROSTER))
        assert len(failures) == 1 and field in failures[0].found, field


def test_organizacion_sin_datos_queda_sin_comprobar_con_la_razon():
    results = check_org_settings(_snapshot(organization=Observed.missing("gh: 401")), ENV, ROSTER)
    assert _statuses(results) == [CheckStatus.UNCHECKED] and "gh: 401" in results[0].detail


# --- equipos ---------------------------------------------------------------------------------------


def test_un_resultado_por_equipo_del_roster_y_los_extra_no_fallan():
    results = check_teams(_snapshot(), ENV, ROSTER)
    assert len(results) == len(ROSTER.slugs) and not _failures(results)


def test_equipo_del_roster_ausente_falla_con_el_slug_como_ambito():
    failures = _failures(check_teams(_snapshot(team_slugs=Observed.of(frozenset({"platform-team"}))), ENV, ROSTER))
    assert [f.scope for f in failures] == ["lt-a"]


# --- App -------------------------------------------------------------------------------------------


def test_app_ausente_falla():
    assert _failures(check_app_installed(_snapshot(app_installations=Observed.of(())), ENV, ROSTER))


def test_otra_app_con_cobertura_total_no_cuenta():
    other = (AppInstallation("otra-app", RepositorySelection.ALL, None),)
    assert _failures(check_app_installed(_snapshot(app_installations=Observed.of(other)), ENV, ROSTER))


def test_seleccion_que_cubre_todos_los_esperados_pasa():
    selected = (AppInstallation(APP_SLUG, RepositorySelection.SELECTED, frozenset(ALL_REPOS)),)
    assert not _failures(check_app_installed(_snapshot(app_installations=Observed.of(selected)), ENV, ROSTER))


def test_seleccion_que_omite_un_repositorio_falla_nombrandolo():
    # Clarify 4 de la spec.
    selected = (AppInstallation(APP_SLUG, RepositorySelection.SELECTED, frozenset(ALL_REPOS) - {"mkt-exp"}),)
    failures = _failures(check_app_installed(_snapshot(app_installations=Observed.of(selected)), ENV, ROSTER))
    assert [f.scope for f in failures] == ["mkt-exp"]


# --- secretos --------------------------------------------------------------------------------------


def test_secreto_con_nombre_casi_igual_cuenta_como_ausente():
    for almost in ("app_id", "APP-ID", "APP_ID "):
        secrets = dict(_snapshot().secret_names_by_repository)
        secrets["standard"] = Observed.of(frozenset({almost, "APP_PRIVATE_KEY"}))
        failures = _failures(check_secrets(_snapshot(secret_names_by_repository=secrets), ENV, ROSTER))
        assert [f.scope for f in failures] == ["standard"] and "APP_ID" in failures[0].expected, almost


def test_repositorio_sin_datos_de_secretos_queda_sin_comprobar_solo_el():
    secrets = dict(_snapshot().secret_names_by_repository)
    secrets["agents-a"] = Observed.missing("gh: 403")
    results = check_secrets(_snapshot(secret_names_by_repository=secrets), ENV, ROSTER)
    unchecked = [r for r in results if r.status is CheckStatus.UNCHECKED]
    assert [r.scope for r in unchecked] == ["agents-a"] and len(results) == len(ALL_REPOS)


# --- variables -------------------------------------------------------------------------------------


def test_canal_cruzado_falla_con_esperado_y_encontrado():
    variables = dict(_snapshot().variables_by_repository)
    variables["mkt"] = Observed.of({"INDEX_CHANNEL": "experimental", "AGENTIC_TOPIC": "agentic-unit"})
    failures = _failures(check_variables(_snapshot(variables_by_repository=variables), ENV, ROSTER))
    assert failures[0].expected == "INDEX_CHANNEL=production" and failures[0].found == "INDEX_CHANNEL=experimental"


def test_variable_ausente_falla_con_encontrado_ausente():
    variables = dict(_snapshot().variables_by_repository)
    variables["mkt-exp"] = Observed.of({"INDEX_CHANNEL": "experimental"})
    failures = _failures(check_variables(_snapshot(variables_by_repository=variables), ENV, ROSTER))
    assert failures[0].found == "ausente" and "AGENTIC_TOPIC" in failures[0].expected


# --- topic -----------------------------------------------------------------------------------------


def test_dominio_sin_topic_falla():
    results = check_topic(_snapshot(repositories_with_topic=Observed.of(frozenset())), ENV, ROSTER)
    assert [f.scope for f in _failures(results)] == ["agents-a"]


def test_repositorio_que_no_es_dominio_con_topic_falla_nombrandolo():
    tagged = Observed.of(frozenset({"agents-a", "repo-de-prueba"}))
    failures = _failures(check_topic(_snapshot(repositories_with_topic=tagged), ENV, ROSTER))
    assert [f.scope for f in failures] == ["repo-de-prueba"]


# --- rulesets --------------------------------------------------------------------------------------


def test_ambos_rulesets_activos_pasan():
    assert not _failures(check_rulesets_present(_snapshot(), ENV, ROSTER))


def test_ruleset_con_otro_nombre_no_cuenta_aunque_tenga_las_mismas_reglas():
    # Clarify 5 de la spec.
    renamed = Ruleset("main-protection", RulesetEnforcement.ACTIVE, RulesetTarget.BRANCH, CONTEXTS)
    snapshot = _snapshot(rulesets_by_repository={"agents-a": Observed.of((renamed, TAGS))})
    failures = _failures(check_rulesets_present(snapshot, ENV, ROSTER))
    assert len(failures) == 1 and "protect-main" in failures[0].expected


def test_ruleset_presente_pero_no_activo_falla():
    for enforcement in (RulesetEnforcement.EVALUATE, RulesetEnforcement.DISABLED):
        inactive = Ruleset("protect-tags", enforcement, RulesetTarget.TAG, ())
        snapshot = _snapshot(rulesets_by_repository={"agents-a": Observed.of((MAIN, inactive))})
        assert _failures(check_rulesets_present(snapshot, ENV, ROSTER)), enforcement


def test_los_tres_contextos_exactos_pasan():
    assert not _failures(check_rulesets_contexts(_snapshot(), ENV, ROSTER))


def test_cada_desviacion_de_los_contextos_falla_mostrando_esperados_y_encontrados():
    # Medido dos veces en la demo anterior: un contexto renombrado bloqueó todos los PR.
    cases = {
        "uno de menos": CONTEXTS[:2],
        "uno de más": CONTEXTS + (RequiredContext("verify / extra", ACTIONS_INTEGRATION_ID),),
        "un carácter distinto": CONTEXTS[:2] + (RequiredContext("verify / colision", ACTIONS_INTEGRATION_ID),),
        "otro integration_id": CONTEXTS[:2] + (RequiredContext(REQUIRED_CONTEXTS[2], 99),),
        "sin integration_id": CONTEXTS[:2] + (RequiredContext(REQUIRED_CONTEXTS[2], None),),
    }
    for label, contexts in cases.items():
        main = Ruleset("protect-main", RulesetEnforcement.ACTIVE, RulesetTarget.BRANCH, contexts)
        snapshot = _snapshot(rulesets_by_repository={"agents-a": Observed.of((main, TAGS))})
        failures = _failures(check_rulesets_contexts(snapshot, ENV, ROSTER))
        assert len(failures) == 1 and failures[0].expected and failures[0].found, label


def test_rulesets_sin_datos_dejan_ambas_comprobaciones_sin_comprobar():
    snapshot = _snapshot(rulesets_by_repository={"agents-a": Observed.missing("gh: 403")})
    for check in (check_rulesets_present, check_rulesets_contexts):
        assert _statuses(check(snapshot, ENV, ROSTER)) == [CheckStatus.UNCHECKED], check.__name__


# --- recorrido -------------------------------------------------------------------------------------


def test_recorre_todas_las_comprobaciones_aunque_la_primera_falle():
    broken = _snapshot(organization=Observed.of(OrganizationSettings("enterprise", "none", True)))
    report = run_checks(broken, ENV, ROSTER)
    ids = {r.check_id for r in report.results}
    assert len(ids) == len(CHECKS) and report.count(CheckStatus.FAILED) == 3
