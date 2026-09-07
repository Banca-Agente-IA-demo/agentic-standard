"""Las plantillas de artefacto no reintroducen el gobierno retirado y nacen cumpliendo el estándar.

Convertido de `check_frontmatter_templates`, `check_evals_template` y `check_hooks_template` del
`selfcheck.py` del paquete de diseño del hito 1, más la comprobación de la lista de eventos portables
(D3), que allí no estaba.
"""

from __future__ import annotations

import json

import pytest
import yaml

from tests.templates.markers import read_template

TEXT_ARTIFACT_TEMPLATES = (
    "artifacts/skill/SKILL.md",
    "artifacts/agent/NAME.agent.md",
    "artifacts/prompt/NAME.prompt.md",
)

# Los siete campos que la demo guardaba en el frontmatter y que hoy viven en el gobierno de la unidad,
# en la etiqueta o en Port. El validador falla si reaparecen; la plantilla es por donde volverían.
GOVERNANCE_FIELDS = frozenset(
    {"id", "owner_team", "owner_contact", "status", "version", "standard_version", "data_classification"}
)

# Eventos que disparan en los dos clientes con la misma grafía, medidos el 7 de septiembre de 2026
# (D3). Un evento fuera de la lista no falla en el cliente: simplemente no dispara nunca, y el autor
# cree que su control está activo.
PORTABLE_HOOK_EVENTS = frozenset(
    {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"}
)

MIN_EVAL_CASES = 3
REQUIRED_EVAL_CATEGORIES = frozenset({"happy_path", "edge_case", "negative"})
DETERMINISTIC_ASSERT_TYPES = frozenset(
    {"contains", "icontains", "not-contains", "regex", "is-json", "javascript"}
)
PLUGIN_ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"


def _frontmatter(relative_path: str) -> dict:
    return yaml.safe_load(read_template(relative_path).split("---", 2)[1])


@pytest.mark.parametrize("template", TEXT_ARTIFACT_TEMPLATES)
def test_ninguna_plantilla_de_artefacto_lleva_gobierno_en_su_frontmatter(template):
    metadata = _frontmatter(template).get("metadata") or {}
    leaked = GOVERNANCE_FIELDS & set(metadata)
    assert not leaked, sorted(leaked)


@pytest.mark.parametrize("template", TEXT_ARTIFACT_TEMPLATES)
def test_el_mapa_de_catalogo_es_texto_a_texto(template):
    # D1: es el formato que define la especificación de skills y el que viaja en los dos clientes.
    metadata = _frontmatter(template).get("metadata") or {}
    assert all(isinstance(value, str) for value in metadata.values()), metadata


@pytest.mark.parametrize("template", TEXT_ARTIFACT_TEMPLATES)
def test_cada_plantilla_de_artefacto_declara_nombre_y_descripcion(template):
    front = _frontmatter(template)
    assert front.get("name") and front.get("description"), front


def test_la_plantilla_de_suite_tiene_al_menos_tres_casos():
    suite = yaml.safe_load(read_template("artifacts/evals/promptfooconfig.yaml"))
    assert len(suite.get("tests") or []) >= MIN_EVAL_CASES


def test_la_plantilla_de_suite_cubre_las_tres_categorias_de_caso():
    # D4: es la forma exigible de «camino esperado, borde y abstención» de 02 §8.2.
    suite = yaml.safe_load(read_template("artifacts/evals/promptfooconfig.yaml"))
    categories = {(test.get("metadata") or {}).get("category") for test in suite["tests"]}
    assert categories == REQUIRED_EVAL_CATEGORIES


def test_cada_caso_de_la_plantilla_de_suite_tiene_una_asercion_mecanica():
    # Un caso sostenido sólo por el juez no dice nada cuando el juez no está disponible.
    suite = yaml.safe_load(read_template("artifacts/evals/promptfooconfig.yaml"))
    for test in suite["tests"]:
        types = {assertion.get("type") for assertion in test.get("assert") or []}
        assert types & DETERMINISTIC_ASSERT_TYPES, test.get("description")


def test_la_plantilla_de_agente_documenta_las_dos_grafias_para_restringir_el_servidor():
    # D7, medido el 7 de septiembre de 2026: no hay una sola grafía portable. Con sólo la de Claude,
    # Copilot arranca el agente sin el servidor y no avisa; con sólo la de Copilot, Claude rehúsa
    # lanzarlo. Cada cliente ignora en silencio la que no entiende, así que van las dos.
    guidance = read_template("artifacts/agent/NAME.agent.md")
    assert "mcp__plugin_" in guidance, "falta la grafía de Claude Code"
    assert "<<SERVER>>/*" in guidance, "falta la grafía de Copilot CLI"


def _hook_actions() -> list[tuple[str, dict]]:
    hooks = json.loads(read_template("artifacts/hooks/hooks.json"))["hooks"]
    return [(event, action) for event, groups in hooks.items() for group in groups for action in group["hooks"]]


def test_la_plantilla_de_hooks_solo_usa_eventos_portables():
    events = {event for event, _ in _hook_actions()}
    assert events <= PORTABLE_HOOK_EVENTS, sorted(events - PORTABLE_HOOK_EVENTS)


def test_cada_accion_de_la_plantilla_de_hooks_declara_tope_de_tiempo():
    # Un hook sin tope puede colgar el cliente de quien lo instale.
    for event, action in _hook_actions():
        assert "timeout" in action, event


def test_el_campo_de_tope_inventado_por_la_demo_no_aparece():
    # `timeoutSec` no existe en el formato; la demo lo aceptaba «durante la migración» y aquí es error
    # desde el primer día porque la organización nace limpia.
    for event, action in _hook_actions():
        assert "timeoutSec" not in action, event


def test_cada_comando_de_la_plantilla_de_hooks_apunta_dentro_de_la_unidad():
    # C5: una ruta absoluta no existe en la máquina de nadie más y ejecuta algo que no se selló.
    for event, action in _hook_actions():
        assert str(action.get("command", "")).startswith(PLUGIN_ROOT_PREFIX), event
