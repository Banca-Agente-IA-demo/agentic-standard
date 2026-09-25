"""La frontera exterior rechaza lo que no puede sembrarse, y lo hace nombrando el campo.

Son pruebas de dominio puro: reciben datos y comparan el resultado, sin disco y sin dobles (T1).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from unit_seed.errors import InvalidRequestError
from unit_seed.unit_kinds import ArtifactType, RiskLevel, UnitForm
from unit_seed.unit_request import MAX_ARTIFACTS_PER_TYPE, UnitRequest

GROUPED_PAYLOAD = {
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


def test_los_campos_numerados_del_formulario_se_colapsan_en_listas() -> None:
    # Port no ofrece un campo repetible, así que la acción declara skill_1, skill_2, ... y la
    # frontera es el sitio donde esa forma de formulario se convierte en la forma de dominio.
    request = UnitRequest.model_validate(GROUPED_PAYLOAD)
    for field, expected in (("skills", 2), ("agents", 2), ("prompts", 2), ("mcp_servers", 0)):
        assert len(getattr(request, field)) == expected, field


def test_los_huecos_entre_campos_numerados_no_dejan_nombres_vacios() -> None:
    # El autor puede rellenar el 1 y el 3 y dejar el 2 en blanco; un nombre vacío sembraría un
    # archivo llamado `.agent.md`.
    payload = {**GROUPED_PAYLOAD, "skill_2": "   ", "skill_3": "cnf-project-scaffolding"}
    assert UnitRequest.model_validate(payload).skills == (
        "cnf-limitations-and-alternatives", "cnf-project-scaffolding")


def test_un_nombre_de_agente_con_punto_se_admite() -> None:
    # Medido el 24 de septiembre de 2026 en Copilot CLI 1.0.87: un agente llamado
    # `atla.cnf-migrator.analyst` carga y se cualifica como `plugin:atla.cnf-migrator.analyst`.
    # Es la convención real de BCP, `{app}.{dominio}.{rol}`, y sin esto no se puede sembrar.
    assert "atla.cnf-migrator.analyst" in UnitRequest.model_validate(GROUPED_PAYLOAD).agents


def test_un_nombre_de_skill_con_punto_es_error() -> None:
    # La forma del nombre del skill la fija la especificación de Agent Skills, no este estándar, y el
    # nombre es además el de su directorio.
    payload = {**GROUPED_PAYLOAD, "skill_1": "atlas.to.cnf.vault"}
    with pytest.raises(InvalidRequestError, match="skill"):
        UnitRequest.model_validate(payload)


def test_cada_forma_invalida_de_nombre_de_artefacto_se_rechaza() -> None:
    for bad_name in ("Revisor PR", "agente..doble", ".inicio", "fin.", "plugin:agente", "CON-MAYUS"):
        payload = {**GROUPED_PAYLOAD, "agent_1": bad_name}
        with pytest.raises(InvalidRequestError):
            UnitRequest.model_validate(payload)
        assert True, bad_name


def test_dos_artefactos_del_mismo_tipo_con_el_mismo_nombre_es_error() -> None:
    # Se sembrarían en la misma ruta: el segundo sobreescribiría al primero sin avisar.
    payload = {**GROUPED_PAYLOAD, "skill_2": "cnf-limitations-and-alternatives"}
    with pytest.raises(InvalidRequestError, match="repetidos"):
        UnitRequest.model_validate(payload)


def test_una_unidad_individual_sin_tipo_de_artefacto_es_error() -> None:
    payload = {**GROUPED_PAYLOAD, "unit_form": "individual"}
    with pytest.raises(InvalidRequestError, match="tipo de artefacto"):
        UnitRequest.model_validate(payload)


def test_un_servidor_mcp_sin_equipo_responsable_es_error() -> None:
    # `accountable_team` es obligatorio siempre, tenga o no credenciales el servidor: es quien avala
    # que ese endpoint externo puede recibir datos del banco.
    payload = {**GROUPED_PAYLOAD, "mcp_server_1": "jira"}
    with pytest.raises(InvalidRequestError, match="responsable"):
        UnitRequest.model_validate(payload)


def test_un_nivel_de_riesgo_que_no_existe_se_rechaza_nombrando_el_campo() -> None:
    payload = {**GROUPED_PAYLOAD, "risk_level": "critical"}
    with pytest.raises(ValidationError, match="risk_level"):
        UnitRequest.model_validate(payload)


def test_los_enumerados_llegan_como_tipos_y_no_como_cadenas() -> None:
    request = UnitRequest.model_validate(GROUPED_PAYLOAD)
    assert request.unit_form is UnitForm.GROUPED
    assert request.risk_level is RiskLevel.MEDIUM


def test_la_peticion_no_se_puede_modificar_despues_de_validarse() -> None:
    # Lo que cruza la frontera queda cerrado: ningún paso posterior reescribe lo que el autor pidió.
    request = UnitRequest.model_validate(GROUPED_PAYLOAD)
    with pytest.raises(ValidationError):
        request.name = "otro-nombre"


def test_el_formulario_admite_tantos_artefactos_por_tipo_como_campos_declara_la_accion() -> None:
    # Si la acción crece a más posiciones y esta constante no, los últimos campos del formulario se
    # perderían en silencio. Una regla verde y una muerta se ven igual.
    payload = {**GROUPED_PAYLOAD}
    for position in range(1, MAX_ARTIFACTS_PER_TYPE + 1):
        payload["skill_%d" % position] = "skill-numero-%d" % position
    assert len(UnitRequest.model_validate(payload).skills) == MAX_ARTIFACTS_PER_TYPE


def test_el_tipo_de_artefacto_individual_llega_como_enumerado() -> None:
    payload = {**GROUPED_PAYLOAD, "unit_form": "individual", "artifact_type": "skill"}
    assert UnitRequest.model_validate(payload).artifact_type is ArtifactType.SKILL
