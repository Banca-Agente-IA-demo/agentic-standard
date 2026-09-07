"""El lector de gh parsea las respuestas reales medidas (fixtures/README.md) con un runner falso (T3, T4)."""

from pathlib import Path

from smoke_org.gh_reader import CommandOutput, GhReader
from smoke_org.model import RepositorySelection, RulesetEnforcement

FIXTURES = Path(__file__).parent / "fixtures"
ORG = "Banca-Agente-IA-demo"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeRunner:
    """Devuelve una salida por comando exacto y registra lo que se le pidió."""

    def __init__(self, outputs: dict[str, CommandOutput]) -> None:
        self._outputs = outputs
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str]) -> CommandOutput:
        self.commands.append(command)
        key = " ".join(command)
        if key not in self._outputs:
            raise AssertionError(f"comando no previsto por la prueba: {key}")
        return self._outputs[key]


def _ok(stdout: str) -> CommandOutput:
    return CommandOutput(0, stdout, "")


def test_parsea_los_ajustes_de_la_organizacion():
    runner = FakeRunner({f"gh api orgs/{ORG}": _ok(_fixture("org.json"))})
    settings = GhReader(ORG, runner).organization().value
    assert (settings.plan, settings.default_repository_permission, settings.members_can_create_repositories) == (
        "free", "read", False,
    )


def test_parsea_los_slugs_de_los_equipos_paginando():
    runner = FakeRunner({f"gh api orgs/{ORG}/teams --paginate": _ok(_fixture("teams.json"))})
    slugs = GhReader(ORG, runner).team_slugs().value
    assert "lt-modernization" in slugs and len(slugs) == 7


def test_parsea_la_instalacion_de_la_app_con_cobertura_total_sin_segunda_llamada():
    runner = FakeRunner({f"gh api orgs/{ORG}/installations": _ok(_fixture("installations.json"))})
    installations = GhReader(ORG, runner).app_installations().value
    assert installations[0].app_slug == "agentic-lifecycle"
    assert installations[0].repository_selection is RepositorySelection.ALL
    assert len(runner.commands) == 1


def test_parsea_los_nombres_de_los_secretos():
    runner = FakeRunner({f"gh secret list --repo {ORG}/agentic-standard --json name": _ok(_fixture("secret_list.json"))})
    assert GhReader(ORG, runner).secret_names("agentic-standard").value == {"APP_ID", "APP_PRIVATE_KEY"}


def test_parsea_las_variables_con_su_valor():
    key = f"gh variable list --repo {ORG}/agentic-marketplace --json name,value"
    runner = FakeRunner({key: _ok(_fixture("variable_list.json"))})
    assert GhReader(ORG, runner).variables("agentic-marketplace").value == {
        "INDEX_CHANNEL": "production",
        "AGENTIC_TOPIC": "agentic-unit",
    }


def test_parsea_los_repositorios_con_topic():
    key = f"gh repo list {ORG} --topic agentic-unit --json name --limit 1000"
    runner = FakeRunner({key: _ok(_fixture("repo_list_topic.json"))})
    assert GhReader(ORG, runner).repositories_with_topic("agentic-unit").value == {"agents-modernization"}


def test_pide_el_detalle_de_cada_ruleset_porque_la_lista_no_trae_reglas():
    # Medido el 2026-09-07: gh api repos/.../rulesets devuelve id, name, enforcement y target, sin rules.
    repo = "agents-modernization"
    runner = FakeRunner(
        {
            f"gh api repos/{ORG}/{repo}/rulesets": _ok(_fixture("rulesets_list.json")),
            f"gh api repos/{ORG}/{repo}/rulesets/22463950": _ok(_fixture("ruleset_protect_main.json")),
            f"gh api repos/{ORG}/{repo}/rulesets/22463954": _ok(_fixture("ruleset_protect_tags.json")),
        }
    )
    rulesets = GhReader(ORG, runner).rulesets(repo).value
    by_name = {r.name: r for r in rulesets}
    assert by_name["protect-main"].enforcement is RulesetEnforcement.ACTIVE
    assert [c.context for c in by_name["protect-main"].required_contexts] == [
        "verify / rules", "verify / evals-verdict", "verify / collision",
    ]
    assert all(c.integration_id == 15368 for c in by_name["protect-main"].required_contexts)
    assert by_name["protect-tags"].required_contexts == ()
    assert len(runner.commands) == 3


def test_credenciales_invalidas_devuelven_unavailable_con_el_mensaje_de_gh():
    # Medido con GH_TOKEN=invalid: cuerpo JSON en stdout, resumen en stderr, código 1.
    runner = FakeRunner(
        {f"gh api orgs/{ORG}/installations": CommandOutput(1, _fixture("gh_unauthorized.json"), "gh: Bad credentials (HTTP 401)")}
    )
    observed = GhReader(ORG, runner).app_installations()
    assert observed.value is None and "Bad credentials" in observed.unavailable.reason


def test_error_sin_cuerpo_json_usa_la_ultima_linea_de_stderr():
    runner = FakeRunner({f"gh api orgs/{ORG}": CommandOutput(4, "", "To get started with GitHub CLI, please run:  gh auth login\n")})
    observed = GhReader(ORG, runner).organization()
    assert observed.value is None and "gh auth login" in observed.unavailable.reason


def test_los_comandos_se_construyen_como_listas_sin_concatenar():
    runner = FakeRunner({f"gh secret list --repo {ORG}/agentic-standard --json name": _ok("[]")})
    GhReader(ORG, runner).secret_names("agentic-standard")
    assert runner.commands == [["gh", "secret", "list", "--repo", f"{ORG}/agentic-standard", "--json", "name"]]
