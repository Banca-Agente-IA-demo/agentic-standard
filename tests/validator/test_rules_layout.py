"""Layout de la unidad (04 §4) e higiene del contenido versionado (C2)."""

from __future__ import annotations

from agentic_validator.domain.rules import layout

from tests.validator.units import hooks_config, snapshot


def _rules(snap) -> list[str]:
    findings = (
        layout.check_no_nested_unit(snap)
        + layout.check_artifacts_are_in_their_directory(snap)
        + layout.check_hooks_bring_tests(snap)
        + layout.check_no_absolute_paths(snap)
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


def test_una_unidad_individual_lleva_su_artefacto_en_la_raiz_y_no_es_error():
    assert _rules(snapshot(files=("SKILL.md", "GOVERNANCE.json"))) == []


def test_unos_hooks_sin_pruebas_son_error():
    # C5: es el único tipo que ejecuta código propio sin que nadie lo invoque.
    snap = snapshot(hooks=hooks_config(), files=("hooks/hooks.json", "hooks/scripts/check.sh"))
    assert "layout.hooks-without-tests" in _rules(snap)


def test_unos_hooks_con_pruebas_no_producen_hallazgo():
    files = ("hooks/hooks.json", "hooks/scripts/check.sh", "hooks/tests/test_check.sh")
    assert "layout.hooks-without-tests" not in _rules(snapshot(hooks=hooks_config(), files=files))


def test_una_ruta_absoluta_en_un_archivo_ejecutable_es_error():
    # Sólo existe en la máquina de quien la escribió.
    for ruta in ("/home/ana/scripts/x.sh", "C:\\Users\\ana\\x.ps1", "/usr/local/bin/tool"):
        contents = {"hooks/scripts/check.sh": f"#!/bin/sh\n{ruta} --run\n"}
        assert "hygiene.absolute-path" in _rules(snapshot(text_contents=contents)), ruta


def test_una_ruta_de_la_unidad_no_es_una_ruta_absoluta():
    contents = {"hooks/scripts/check.sh": "#!/bin/sh\n${CLAUDE_PLUGIN_ROOT}/hooks/scripts/otro.sh\n"}
    assert _rules(snapshot(text_contents=contents)) == []


def test_una_ruta_en_la_prosa_de_un_documento_no_se_juzga():
    # En un README una ruta suele ser un ejemplo; el ruido ahí no aporta.
    contents = {"README.md": "Instálalo en /usr/local/share si quieres.\n"}
    assert _rules(snapshot(text_contents=contents)) == []
