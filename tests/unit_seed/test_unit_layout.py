"""Cada artefacto se siembra donde el documento 01 dice, y su posición no es estilo sino contrato.

Pruebas de dominio puro: ninguna toca disco (T1).
"""

from __future__ import annotations

from unit_seed.unit_kinds import ArtifactType
from unit_seed.unit_layout import (declared_artifacts, hooks_path, manifest_path, mcp_config_path,
                                   seeds_hooks, seeds_mcp_config, unit_dir)
from unit_seed.unit_request import UnitRequest

BASE = {
    "name": "cnf-migration-flow",
    "description": "Audita un microservicio Atlas y planifica su migracion a CNF.",
    "owner_team": "squad-cnf-migration",
    "team_mailbox": "squad-cnf-migration@bcp.com.pe",
    "risk_level": "medium",
    "repository": "Banca-Agente-IA-demo/agents-modernization",
}


def _grouped(**extra: object) -> UnitRequest:
    return UnitRequest.model_validate({**BASE, "unit_form": "grouped", **extra})


def _individual(artifact_type: str, **extra: object) -> UnitRequest:
    return UnitRequest.model_validate(
        {**BASE, "unit_form": "individual", "artifact_type": artifact_type, **extra})


def test_una_unidad_agrupada_vive_bajo_plugins() -> None:
    assert unit_dir(_grouped()).as_posix() == "plugins/cnf-migration-flow"


def test_cada_tipo_individual_vive_bajo_el_directorio_de_su_tipo() -> None:
    expected = {
        "skill": "skills/cnf-migration-flow",
        "agent": "agents/cnf-migration-flow",
        "prompt": "commands/cnf-migration-flow",
        "hooks": "hooks/cnf-migration-flow",
        "mcp": "mcps/cnf-migration-flow",
    }
    for artifact_type, path in expected.items():
        assert unit_dir(_individual(artifact_type)).as_posix() == path, artifact_type


def test_el_manifiesto_esta_en_el_mismo_sitio_en_las_dos_formas() -> None:
    # Documento 01 §1: las dos formas llevan exactamente los mismos manifiestos. De ahí que haya una
    # sola plantilla y no dos idénticas.
    assert manifest_path(_grouped()).name == manifest_path(_individual("skill")).name
    for request in (_grouped(), _individual("skill")):
        assert manifest_path(request).parent.name == ".claude-plugin"


def test_el_mcp_json_va_en_la_raiz_de_la_unidad() -> None:
    # Los clientes NO descienden a subcarpetas: uno dentro de skills/ no falla, simplemente no se
    # lee. Por eso su posición es funcional y no una convención.
    assert mcp_config_path(_grouped()) == unit_dir(_grouped()) / ".mcp.json"


def test_los_hooks_van_en_su_subcarpeta_tambien_en_la_forma_individual() -> None:
    # Medido el 16 de septiembre de 2026: aplanado a la raíz, Claude Code no lo registra ni dispara,
    # y el plugin queda instalado sin avisar de nada.
    assert hooks_path(_individual("hooks")).as_posix().endswith("hooks/hooks.json")


def test_el_artefacto_de_una_unidad_individual_se_llama_como_la_unidad() -> None:
    # No es una decisión del autor: es la identidad de la unidad, y de ahí sale que el nombre
    # aparezca en cuatro sitios a la vez.
    artifacts = declared_artifacts(_individual("skill"))
    assert len(artifacts) == 1
    assert artifacts[0].name == "cnf-migration-flow"


def test_una_unidad_individual_de_mcp_o_de_hooks_no_declara_artefactos_con_archivo_propio() -> None:
    for artifact_type in ("mcp", "hooks"):
        assert declared_artifacts(_individual(artifact_type)) == (), artifact_type


def test_una_unidad_agrupada_declara_sus_tres_tipos_con_comportamiento() -> None:
    request = _grouped(skill_1="atlas-to-cnf-vault",
                       agent_1="atla.cnf-migrator.analyst",
                       prompt_1="atla.cnf-migration.analyze")
    kinds = [artifact.kind for artifact in declared_artifacts(request)]
    assert kinds == [ArtifactType.SKILL, ArtifactType.AGENT, ArtifactType.PROMPT]


def test_cada_artefacto_de_una_agrupada_tiene_su_propia_carpeta_de_evals() -> None:
    request = _grouped(skill_1="atlas-to-cnf-vault", skill_2="cnf-limitations-and-alternatives")
    suites = {artifact.eval_path.as_posix() for artifact in declared_artifacts(request)}
    assert suites == {
        "plugins/cnf-migration-flow/evals/atlas-to-cnf-vault/promptfooconfig.yaml",
        "plugins/cnf-migration-flow/evals/cnf-limitations-and-alternatives/promptfooconfig.yaml",
    }


def test_la_suite_de_una_unidad_individual_no_lleva_subcarpeta() -> None:
    # Tiene un solo artefacto, así que no hay nada de lo que distinguirla.
    artifact = declared_artifacts(_individual("skill"))[0]
    assert artifact.eval_path.as_posix() == (
        "skills/cnf-migration-flow/evals/promptfooconfig.yaml")


def test_una_unidad_individual_de_mcp_declara_un_servidor_con_su_propio_nombre() -> None:
    assert seeds_mcp_config(_individual("mcp")) == ("cnf-migration-flow",)


def test_sin_servidores_declarados_no_se_siembra_mcp_json() -> None:
    # Una carpeta o un archivo vacío mienten: sugieren que la unidad tiene algo que no tiene.
    assert seeds_mcp_config(_grouped()) == ()


def test_los_hooks_se_siembran_si_se_marcaron_o_si_la_unidad_es_de_hooks() -> None:
    for request, expected in ((_grouped(), False),
                              (_grouped(has_hooks=True), True),
                              (_individual("hooks"), True),
                              (_individual("skill"), False)):
        assert seeds_hooks(request) is expected, request.unit_form
