"""El contrato de GOVERNANCE.json: nueve campos, ni uno más, y las cotas de las decisiones D2 y D6.

Convertido de `check_governance` del `selfcheck.py` del paquete de diseño del hito 1 (7 de septiembre
de 2026), con un nombre por defecto cubierto (T2).
"""

from __future__ import annotations

import copy

from tests.schemas.conftest import errors_of

# Campos de primer nivel que la demo anterior guardaba aquí y que hoy se derivan de un hecho. La
# revisión del hito 1 los retiró uno a uno; el esquema es lo único que impide que vuelvan.
RETIRED_FIELDS = (
    "domain",
    "status",
    "version",
    "standard_version",
    "artifacts",
    "certification",
    "distribution",
    "registry",
    "$schema",
)
REQUIRED_FIELDS = ("schema_version", "id", "owner", "data_classification", "permissions")


def test_una_unidad_agrupada_completa_es_valida(governance_validator, complete_governance):
    assert errors_of(governance_validator, complete_governance) == []


def test_una_unidad_individual_obsoleta_sin_sucesor_es_valida(governance_validator, minimal_governance):
    assert errors_of(governance_validator, minimal_governance) == []


def test_cada_campo_retirado_de_la_demo_que_reaparezca_es_error(governance_validator, complete_governance):
    for field in RETIRED_FIELDS:
        errors = errors_of(governance_validator, {**complete_governance, field: "x"})
        assert any("Additional properties" in e for e in errors), field


def test_falta_cada_campo_obligatorio_produce_un_error(governance_validator, complete_governance):
    for field in REQUIRED_FIELDS:
        incomplete = {k: v for k, v in complete_governance.items() if k != field}
        errors = errors_of(governance_validator, incomplete)
        assert any("required property" in e for e in errors), field


def test_id_con_la_forma_antigua_de_puntos_es_error(governance_validator, complete_governance):
    # La demo usaba <org>.<dominio>.<nombre>; hoy es repo/name y el dominio se deriva del repositorio.
    bad = {**complete_governance, "id": "acme.sdlc.migracion"}
    assert any("does not match" in e for e in errors_of(governance_validator, bad))


def test_schema_version_desconocida_es_error(governance_validator, complete_governance):
    bad = {**complete_governance, "schema_version": "2.0"}
    assert any("is not one of" in e for e in errors_of(governance_validator, bad))


def test_un_comodin_en_los_permisos_es_error(governance_validator, complete_governance):
    # C1 exige permisos mínimos: un patrón del cliente como Bash(git:*) vale, un * suelto no.
    for field in ("tools", "commands"):
        bad = copy.deepcopy(complete_governance)
        bad["permissions"][field] = ["*"]
        assert any("does not match" in e for e in errors_of(governance_validator, bad)), field


def test_dos_servidores_mcp_en_una_unidad_es_error(governance_validator, complete_governance):
    # D2: la aprobación de Ciberseguridad y Riesgo operacional es de un contrato, no de dos.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["confluence"] = copy.deepcopy(bad["mcp"]["jira"])
    assert any("too many properties" in e for e in errors_of(governance_validator, bad))


def test_dos_servidores_en_permissions_mcp_servers_es_error(governance_validator, complete_governance):
    bad = copy.deepcopy(complete_governance)
    bad["permissions"]["mcp_servers"] = ["jira", "confluence"]
    assert any("too long" in e for e in errors_of(governance_validator, bad))


def test_credenciales_declaradas_sin_custodio_es_error(governance_validator, complete_governance):
    # D2: sin custodio, quien instala acaba pidiendo el acceso a ciegas.
    bad = copy.deepcopy(complete_governance)
    del bad["mcp"]["jira"]["credentials_owner"]
    assert any("credentials_owner" in e for e in errors_of(governance_validator, bad))


def test_un_servidor_sin_credenciales_no_necesita_custodio(governance_validator, complete_governance):
    ok = copy.deepcopy(complete_governance)
    ok["mcp"]["jira"]["credentials"] = []
    del ok["mcp"]["jira"]["credentials_owner"]
    assert errors_of(governance_validator, ok) == []


def test_tools_digest_sin_el_prefijo_sha256_es_error(governance_validator, complete_governance):
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["tools_digest"] = "3f9a" * 16
    assert any("does not match" in e for e in errors_of(governance_validator, bad))


def test_el_bloque_approval_de_la_demo_dentro_de_mcp_es_error(governance_validator, complete_governance):
    # La aprobación vive en la solicitud de cambio y su fecha de revisión en Port, no en el archivo.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["approval"] = {"approved_by": "x"}
    assert any("Additional properties" in e for e in errors_of(governance_validator, bad))


def test_risk_level_fuera_del_enumerado_es_error(governance_validator, complete_governance):
    bad = {**complete_governance, "risk_level": "critical"}
    assert any("is not one of" in e for e in errors_of(governance_validator, bad))


def test_falta_cada_campo_de_deprecation_produce_un_error(governance_validator, minimal_governance):
    # D6: los tres son obligatorios cuando el bloque existe; un campo ausente no distinguiría una
    # decisión de un olvido.
    for field in ("superseded_by", "sunset_date", "decided_by"):
        bad = copy.deepcopy(minimal_governance)
        del bad["deprecation"][field]
        errors = errors_of(governance_validator, bad)
        assert any("required property" in e for e in errors), field


def test_sunset_date_que_no_es_iso_es_error(governance_validator, minimal_governance):
    bad = copy.deepcopy(minimal_governance)
    bad["deprecation"]["sunset_date"] = "31/03/2027"
    assert any("date" in e for e in errors_of(governance_validator, bad))


def test_superseded_by_admite_none_como_decision_explicita(governance_validator, minimal_governance):
    # D6: «lo pensé y no hay reemplazo» es una decisión, y el asistente la ofrece en el menú.
    assert minimal_governance["deprecation"]["superseded_by"] == "none"
    assert errors_of(governance_validator, minimal_governance) == []


def test_un_contacto_que_no_es_correo_es_error(governance_validator, complete_governance):
    bad = copy.deepcopy(complete_governance)
    bad["owner"]["contact"] = "squad-sdlc"
    assert any("email" in e for e in errors_of(governance_validator, bad))


def test_x_extensions_admite_cualquier_contenido(governance_validator, complete_governance):
    # Es la válvula de escape declarada: lo exclusivo de un cliente cabe aquí sin validación.
    ok = {**complete_governance, "x_extensions": {"copilot": {"hooks": ["userPromptSubmitted"]}}}
    assert errors_of(governance_validator, ok) == []
