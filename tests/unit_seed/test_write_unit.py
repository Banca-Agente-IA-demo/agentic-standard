"""La siembra escribe lo que dice que escribe, desde las plantillas reales del repositorio.

Es la única parte del sembrador que toca disco, así que es la única que usa `tmp_path`. Las
plantillas son las de verdad y no dobles: lo que se comprueba aquí es que el código y las plantillas
siguen encajando, que es justo lo que se rompió cuando se retiró `GOVERNANCE.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unit_seed.errors import TemplateNotFoundError
from unit_seed.unit_request import UnitRequest
from unit_seed.write_unit import write_unit

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"

DEMO_PAYLOAD = {
    "name": "cnf-migration-flow",
    "description": "Audita un microservicio Atlas y planifica su migracion a CNF.",
    "owner_team": "squad-cnf-migration",
    "team_mailbox": "squad-cnf-migration@bcp.com.pe",
    "risk_level": "medium",
    "unit_form": "grouped",
    "skill_1": "cnf-limitations-and-alternatives",
    "skill_2": "atlas-to-cnf-vault",
    "agent_1": "atla.cnf-migrator.analyst",
    "agent_2": "atla.cnf-migrator.planner",
    "prompt_1": "atla.cnf-migration.analyze",
    "prompt_2": "atla.cnf-migration.plan",
    "repository": "Banca-Agente-IA-demo/agents-modernization",
}

# Seis artefactos con comportamiento: manifiesto, seis archivos y seis suites.
DEMO_FILES = 1 + 6 + 6


def _seed(tmp_path: Path, **extra: object) -> tuple[Path, ...]:
    request = UnitRequest.model_validate({**DEMO_PAYLOAD, **extra})
    return write_unit(request, TEMPLATES, tmp_path)


def test_la_unidad_de_la_demo_siembra_trece_archivos_y_ni_uno_mas(tmp_path: Path) -> None:
    # El recuento es la parte que importa: sin él, un recorrido que deja de escribir suites pasaría
    # en verde sin escribir nada. Una regla verde y una muerta se ven igual.
    written = _seed(tmp_path)
    assert len(written) == DEMO_FILES, [path.name for path in written]


def test_cada_artefacto_con_comportamiento_trae_su_suite(tmp_path: Path) -> None:
    _seed(tmp_path)
    unit = tmp_path / "plugins" / "cnf-migration-flow"
    for name in ("cnf-limitations-and-alternatives", "atlas-to-cnf-vault",
                 "atla.cnf-migrator.analyst", "atla.cnf-migrator.planner",
                 "atla.cnf-migration.analyze", "atla.cnf-migration.plan"):
        assert (unit / "evals" / name / "promptfooconfig.yaml").exists(), name


def test_un_nombre_con_puntos_no_parte_la_ruta_del_archivo(tmp_path: Path) -> None:
    # El archivo pasa a tener varios puntos: `atla.cnf-migrator.analyst.agent.md`. Medido el 24 de
    # septiembre de 2026 que Copilot recorta solo el sufijo y conserva el nombre entero.
    _seed(tmp_path)
    agents = tmp_path / "plugins" / "cnf-migration-flow" / "agents"
    assert (agents / "atla.cnf-migrator.analyst.agent.md").exists()


def test_el_manifiesto_sembrado_es_json_valido_y_trae_el_gobierno(tmp_path: Path) -> None:
    _seed(tmp_path)
    manifest = json.loads(
        (tmp_path / "plugins" / "cnf-migration-flow" / ".claude-plugin" / "plugin.json")
        .read_text(encoding="utf-8"))
    assert manifest["metadata"]["governance"]["risk_level"] == "medium"
    assert manifest["author"]["email"] == "squad-cnf-migration@bcp.com.pe"


def test_el_esqueleto_no_puede_parecer_terminado(tmp_path: Path) -> None:
    # Una descripción plausible convertiría «sin completar» en indetectable, y el esqueleto tiene que
    # fallar el gate de forma evidente.
    _seed(tmp_path)
    skill = (tmp_path / "plugins" / "cnf-migration-flow" / "skills" / "atlas-to-cnf-vault"
             / "SKILL.md").read_text(encoding="utf-8")
    assert "PENDIENTE" in skill


def test_la_suite_sembrada_conserva_los_marcadores_de_la_plantilla(tmp_path: Path) -> None:
    # Sembrar casos de ejemplo enseñaría a pasar el gate con relleno; sembrar marcadores enseña qué
    # falta y no pasa el gate.
    _seed(tmp_path)
    suite = (tmp_path / "plugins" / "cnf-migration-flow" / "evals" / "atlas-to-cnf-vault"
             / "promptfooconfig.yaml").read_text(encoding="utf-8")
    assert "<<HAPPY_PATH_CASE>>" in suite


def test_sin_servidores_ni_hooks_no_se_siembra_ninguno_de_los_dos(tmp_path: Path) -> None:
    # Un archivo que nadie pidió miente sobre lo que la unidad contiene.
    _seed(tmp_path)
    unit = tmp_path / "plugins" / "cnf-migration-flow"
    for path in (unit / ".mcp.json", unit / "hooks" / "hooks.json"):
        assert not path.exists(), path.name


def test_con_servidores_y_hooks_se_siembran_los_dos(tmp_path: Path) -> None:
    written = _seed(tmp_path, mcp_server_1="jira", mcp_accountable_team="platform-atlassian",
                    has_hooks=True)
    assert len(written) == DEMO_FILES + 2
    unit = tmp_path / "plugins" / "cnf-migration-flow"
    assert json.loads((unit / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"].keys() == {
        "jira"}


def test_una_unidad_individual_siembra_su_skill_en_la_raiz(tmp_path: Path) -> None:
    # Medido el 16 de septiembre de 2026: el SKILL.md va en la raíz de la unidad; el agente y el
    # prompt, en su subcarpeta.
    payload = {key: value for key, value in DEMO_PAYLOAD.items()
               if not key.startswith(("skill_", "agent_", "prompt_"))}
    request = UnitRequest.model_validate(
        {**payload, "unit_form": "individual", "artifact_type": "skill"})
    write_unit(request, TEMPLATES, tmp_path)
    assert (tmp_path / "skills" / "cnf-migration-flow" / "skills" / "cnf-migration-flow"
            / "SKILL.md").exists()


def test_una_plantilla_que_falta_se_nombra_en_vez_de_reventar(tmp_path: Path) -> None:
    # El error dice qué archivo falta: un FileNotFoundError crudo obligaría a leer el traceback.
    request = UnitRequest.model_validate(DEMO_PAYLOAD)
    with pytest.raises(TemplateNotFoundError, match="plantilla"):
        write_unit(request, tmp_path / "no-existe", tmp_path)
