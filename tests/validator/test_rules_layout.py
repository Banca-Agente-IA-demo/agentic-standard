"""Layout de la unidad (04 §4)."""

from __future__ import annotations

from agentic_validator.domain.rules import layout

from tests.validator.units import hooks_config, snapshot


def _rules(snap) -> list[str]:
    findings = (
        layout.check_no_nested_unit(snap)
        + layout.check_artifacts_are_in_their_directory(snap)
        + layout.check_hooks_bring_tests(snap)
    )
    return [f.rule for f in findings]


VALID_FILES = (
    ".claude-plugin/plugin.json",
    "GOVERNANCE.json",
    "skills/demo/SKILL.md",
    "agents/demo.agent.md",
    "commands/demo.prompt.md",
    "evals/demo/promptfooconfig.yaml",
)


def test_un_arbol_como_el_del_lineamiento_no_produce_hallazgos():
    assert _rules(snapshot(files=VALID_FILES)) == []


def test_una_unidad_dentro_de_otra_es_error():
    # Cada unidad publicable se revoca sola; anidarlas rompe esa promesa.
    files = VALID_FILES + ("plugins/otra/GOVERNANCE.json",)
    assert "layout.nested-unit" in _rules(snapshot(files=files))


def test_un_artefacto_fuera_de_su_carpeta_es_error():
    # No falla al instalar: el cliente sencillamente no lo encuentra.
    casos = {
        "un skill": "docs/demo/SKILL.md",
        "un agente": "referencias/demo.agent.md",
        "un prompt": "docs/demo.prompt.md",
    }
    for tipo, ruta in casos.items():
        assert "layout.artifact-outside-its-directory" in _rules(snapshot(files=(ruta,))), tipo


def test_un_skill_individual_en_la_raiz_no_es_error():
    # Medido el 16 de septiembre de 2026 (experimento 6): el SKILL.md en la raíz de la unidad carga y
    # responde en los dos clientes. Es una de las dos excepciones, junto con el .mcp.json.
    assert _rules(snapshot(files=("SKILL.md", "GOVERNANCE.json"))) == []
    assert _rules(snapshot(files=(".mcp.json", "GOVERNANCE.json"))) == []


def test_un_artefacto_aplanado_en_la_raiz_de_una_unidad_individual_es_error():
    # Medido el 16 de septiembre de 2026 (experimento 6) en Claude Code 2.1.272 y Copilot CLI 1.0.85:
    # estas tres formas INSTALAN con mensaje de éxito y no cargan nada, y ningún cliente avisa. El
    # control las dejaba pasar porque saltaba todo lo que estuviera en la raíz de la unidad.
    casos = {
        "un agente": "demo.agent.md",
        "un prompt": "demo.prompt.md",
        "unos hooks": "hooks.json",
    }
    for tipo, ruta in casos.items():
        reglas = _rules(snapshot(files=(ruta, "GOVERNANCE.json")))
        assert "layout.artifact-flattened-at-root" in reglas, tipo


def test_unos_hooks_sin_pruebas_son_error():
    # C5: es el único tipo que ejecuta código propio sin que nadie lo invoque.
    snap = snapshot(hooks=hooks_config(), files=("hooks/hooks.json", "hooks/scripts/check.sh"))
    assert "layout.hooks-without-tests" in _rules(snap)


def test_unos_hooks_con_pruebas_no_producen_hallazgo():
    files = ("hooks/hooks.json", "hooks/scripts/check.sh", "hooks/tests/test_check.sh")
    assert "layout.hooks-without-tests" not in _rules(snapshot(hooks=hooks_config(), files=files))
