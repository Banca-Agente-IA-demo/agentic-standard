"""Artefactos de texto y suites: lo poco que el estándar lee de formatos ajenos."""

from __future__ import annotations

from agentic_validator.domain.model import EvalSuite, Severity, TextArtifact
from agentic_validator.domain.rules import artifacts

from tests.validator.units import snapshot, text_artifact, unit_with_mcp, with_governance


def _findings(snap):
    return (
        artifacts.check_artifact_names(snap)
        + artifacts.check_artifact_descriptions(snap)
        + artifacts.check_no_governance_in_frontmatter(snap)
        + artifacts.check_catalog_metadata_is_text(snap)
        + artifacts.check_agent_mcp_spellings(snap)
        + artifacts.check_external_content_declared(snap)
        + artifacts.check_eval_suites(snap)
    )


def _rules(snap) -> list[str]:
    return [f.rule for f in _findings(snap)]


SKILL = text_artifact("skills/demo/SKILL.md", "demo", name="demo", description="Hace algo. Úsalo cuando toque.")


def test_un_skill_bien_formado_no_produce_hallazgos():
    assert _rules(snapshot(skills=(SKILL,))) == []


def test_un_nombre_que_no_coincide_con_su_ruta_es_error():
    # Si no coinciden, el cliente no encuentra el artefacto: no da error, no aparece.
    bad = text_artifact("skills/demo/SKILL.md", "demo", name="otro", description="x")
    assert "artifact.name-mismatch" in _rules(snapshot(skills=(bad,)))


def test_un_artefacto_sin_descripcion_es_error():
    # Es lo que el modelo lee para decidir si usa el artefacto.
    for description in (None, "", "   "):
        bad = text_artifact("skills/demo/SKILL.md", "demo", name="demo", description=description)
        assert "artifact.description-missing" in _rules(snapshot(skills=(bad,))), repr(description)


def test_un_artefacto_sin_frontmatter_es_error():
    bad = TextArtifact(path="skills/demo/SKILL.md", expected_name="demo")
    assert "artifact.frontmatter-missing" in _rules(snapshot(skills=(bad,)))


def test_un_frontmatter_ilegible_se_informa_como_hallazgo():
    bad = TextArtifact(path="skills/demo/SKILL.md", expected_name="demo", error="mapping values are not allowed")
    assert "artifact.frontmatter-unreadable" in _rules(snapshot(skills=(bad,)))


def test_cada_campo_de_gobierno_que_reaparezca_en_el_frontmatter_es_error():
    # Los siete campos que la demo guardaba aquí y que hoy viven en el gobierno, la etiqueta o Port.
    for field in ("id", "owner_team", "owner_contact", "status", "version", "standard_version", "data_classification"):
        bad = text_artifact("skills/demo/SKILL.md", "demo", name="demo", description="x", **{field: "algo"})
        assert "artifact.governance-in-frontmatter" in _rules(snapshot(skills=(bad,))), field


def test_un_campo_de_gobierno_dentro_del_mapa_de_catalogo_tambien_es_error():
    bad = text_artifact("skills/demo/SKILL.md", "demo", name="demo", description="x", metadata={"version": "1.0"})
    assert "artifact.governance-in-frontmatter" in _rules(snapshot(skills=(bad,)))


def test_un_mapa_de_catalogo_que_no_es_texto_a_texto_es_error():
    # D1: es el formato que define la especificación de skills y el que viaja en los dos clientes.
    bad = text_artifact("skills/demo/SKILL.md", "demo", name="demo", description="x", metadata={"tags": ["a", "b"]})
    assert "artifact.catalog-not-text" in _rules(snapshot(skills=(bad,)))


def test_un_agente_que_restringe_el_servidor_con_las_dos_grafias_no_produce_hallazgo():
    # D7, medido: cada cliente ignora en silencio la grafía que no entiende.
    agent = text_artifact(
        "agents/a.agent.md", "a", name="a", description="x",
        tools=["Read", "mcp__plugin_demo-unit_jira__*", "jira/*"],
    )
    assert "artifact.agent-missing-claude-spelling" not in _rules(unit_with_mcp(agents=(agent,)))
    assert "artifact.agent-missing-copilot-spelling" not in _rules(unit_with_mcp(agents=(agent,)))


def test_un_agente_con_solo_la_grafia_de_claude_es_error():
    # Copilot arranca el agente sin el servidor y no avisa.
    agent = text_artifact("agents/a.agent.md", "a", name="a", description="x", tools=["mcp__plugin_demo-unit_jira__*"])
    assert "artifact.agent-missing-copilot-spelling" in _rules(unit_with_mcp(agents=(agent,)))


def test_un_agente_con_solo_la_grafia_de_copilot_es_error():
    # Claude rehúsa lanzar el agente.
    agent = text_artifact("agents/a.agent.md", "a", name="a", description="x", tools=["jira/*"])
    assert "artifact.agent-missing-claude-spelling" in _rules(unit_with_mcp(agents=(agent,)))


def test_un_agente_sin_tools_en_una_unidad_con_servidor_avisa():
    # Hereda todo lo instalado en la sesión, que es lo contrario de C1.
    agent = text_artifact("agents/a.agent.md", "a", name="a", description="x")
    findings = [f for f in _findings(unit_with_mcp(agents=(agent,))) if f.rule == "artifact.agent-inherits-everything"]
    assert len(findings) == 1 and findings[0].severity is Severity.WARNING


def test_una_unidad_con_artefactos_de_texto_debe_declarar_el_tratamiento_de_contenido_externo():
    # C3 aplica a skill, prompt y agente (03 §3).
    snap = snapshot(governance=with_governance(external_content=None), skills=(SKILL,))
    assert "artifact.external-content-missing" in _rules(snap)


def test_una_unidad_que_solo_expone_un_servidor_no_declara_tratamiento_de_contenido_externo():
    # No interpreta contenido externo, lo expone: C3 no aplica.
    governance = {**unit_with_mcp().governance}
    governance.pop("external_content", None)
    snap = unit_with_mcp(governance=governance)
    assert "artifact.external-content-missing" not in _rules(snap)


def _suite(tests: list) -> EvalSuite:
    return EvalSuite(path="evals/demo/promptfooconfig.yaml", content={"tests": tests})


def _case(category: str, assert_type: str = "icontains") -> dict:
    return {"description": f"caso {category}", "metadata": {"category": category}, "assert": [{"type": assert_type, "value": "x"}]}


VALID_SUITE = _suite([_case("happy_path"), _case("edge_case"), _case("negative")])


def test_una_suite_completa_no_produce_hallazgos():
    assert _rules(snapshot(eval_suites=(VALID_SUITE,))) == []


def test_una_suite_con_menos_de_tres_casos_es_error():
    assert "evals.too-few-cases" in _rules(snapshot(eval_suites=(_suite([_case("happy_path")]),)))


def test_una_suite_a_la_que_le_falta_una_categoria_es_error():
    # D4: es la forma exigible de «camino esperado, borde y abstención» de 02 §8.2.
    suite = _suite([_case("happy_path"), _case("edge_case"), _case("happy_path")])
    assert "evals.missing-categories" in _rules(snapshot(eval_suites=(suite,)))


def test_un_caso_sin_categoria_es_error():
    suite = _suite([_case("happy_path"), _case("edge_case"), {"description": "sin", "assert": [{"type": "regex"}]}])
    assert "evals.case-without-category" in _rules(snapshot(eval_suites=(suite,)))


def test_un_caso_sostenido_solo_por_el_juez_es_error():
    # Cuando el juez no está disponible, un caso con ancla sigue dando información y uno sin ancla no.
    suite = _suite([_case("happy_path"), _case("edge_case"), _case("negative", assert_type="llm-rubric")])
    assert "evals.case-without-deterministic-assertion" in _rules(snapshot(eval_suites=(suite,)))


def test_una_unidad_sin_suite_no_produce_hallazgos_en_esta_capacidad():
    # La suite se exige para publicar, y eso lo comprueba la verificación de la solicitud de cambio.
    assert _rules(snapshot(skills=(SKILL,))) == []
