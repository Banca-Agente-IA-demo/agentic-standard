"""El contrato de GOVERNANCE.json: nueve campos, ni uno más, y las cotas de las decisiones D2 y D6.

Convertido de `check_governance` del `selfcheck.py` del paquete de diseño del hito 1 (7 de septiembre
de 2026), con un nombre por defecto cubierto (T2).
"""

from __future__ import annotations

import copy

from tests.support import errors_of

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


def test_el_equipo_responsable_es_un_slug_y_no_un_objeto(governance_validator, complete_governance):
    # Medido el 16 de septiembre de 2026: el esquema lo tenía como objeto con team y
    # access_request_url, y el contrato lo define como un texto. La URL es propiedad del equipo
    # custodio y no de la unidad: se repetiría en cada unidad que use el mismo servidor, y un release
    # es inmutable mientras que una dirección de ITSM no.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["accountable_team"] = {"team": "platform-atlassian",
                                              "access_request_url": "https://ejemplo/acceso"}
    assert errors_of(governance_validator, bad)


def test_un_servidor_sin_equipo_responsable_es_error(governance_validator, complete_governance):
    # Decidido el 17 de septiembre de 2026: TODO servidor declara quién responde por él, tenga
    # credenciales o no. Antes se eximía a los servidores sin autenticación, y eso dejaba entrar
    # endpoints externos sin que nadie los avalara.
    bad = copy.deepcopy(complete_governance)
    del bad["mcp"]["jira"]["accountable_team"]
    assert any("accountable_team" in e for e in errors_of(governance_validator, bad))


def test_no_se_declaran_las_credenciales_que_el_servidor_necesita(governance_validator,
                                                                  complete_governance):
    # El array `credentials` se retiró el 16 de septiembre de 2026: repetía los ${VAR} que ya están en
    # el .mcp.json, y su regla de que una lista no vacía eleva el riesgo mínimo contradecía que
    # risk_level no derive nada.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["credentials"] = ["JIRA_TOKEN"]
    assert errors_of(governance_validator, bad)


def test_falta_risk_level_es_error(governance_validator, complete_governance):
    # Obligatorio desde el 16 de septiembre de 2026: un campo de catálogo que la mitad de las unidades
    # no trae deja la pregunta «cuántas unidades de riesgo alto hay» con una respuesta parcial que
    # parece completa.
    bad = {k: v for k, v in complete_governance.items() if k != "risk_level"}
    assert any("risk_level" in e for e in errors_of(governance_validator, bad))


def test_el_digest_sin_el_prefijo_sha256_es_error(governance_validator, complete_governance):
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["tools_contract"]["digest"] = "3f9a" * 16
    assert any("does not match" in e for e in errors_of(governance_validator, bad))


def test_falta_cada_pieza_de_lo_observado_produce_un_error(governance_validator, complete_governance):
    # Las tres salen de la misma consulta al servidor. Que falte una significa que el bloque se
    # escribió a mano, que es justo lo que se quiso impedir el 17 de septiembre de 2026.
    for field in ("digest", "write_operations", "observed_at"):
        bad = copy.deepcopy(complete_governance)
        del bad["mcp"]["jira"]["tools_contract"][field]
        assert errors_of(governance_validator, bad), f"no se detectó la falta de {field}"


def test_write_operations_fuera_de_lo_observado_es_error(governance_validator, complete_governance):
    # Suelto entre campos que teclea una persona parecía tecleable, y la plantilla lo confirmaba
    # dándole un `false` por defecto que llegaba a la solicitud sin que nadie mirara el servidor.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["write_operations"] = False
    assert any("Additional properties" in e for e in errors_of(governance_validator, bad))


def test_el_bloque_approval_de_la_demo_dentro_de_mcp_es_error(governance_validator, complete_governance):
    # La aprobación vive en la solicitud de cambio y su fecha de revisión en Port, no en el archivo.
    bad = copy.deepcopy(complete_governance)
    bad["mcp"]["jira"]["approval"] = {"approved_by": "x"}
    assert any("Additional properties" in e for e in errors_of(governance_validator, bad))


def test_risk_level_fuera_del_enumerado_es_error(governance_validator, complete_governance):
    bad = {**complete_governance, "risk_level": "critical"}
    assert any("is not one of" in e for e in errors_of(governance_validator, bad))


def test_falta_cada_campo_de_deprecation_produce_un_error(governance_validator, minimal_governance):
    # D6: los dos son obligatorios cuando el bloque existe; un campo ausente no distinguiría una
    # decisión de un olvido. `decided_by` se retiró el 16 de septiembre de 2026: quién decidió es un
    # hecho que vive en la aprobación de la solicitud de cambio, no un campo que alguien teclea.
    for field in ("superseded_by", "sunset_date"):
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


def test_el_esquema_esta_cerrado_y_no_hay_valvula_de_escape(governance_validator,
                                                            complete_governance):
    # `x_extensions` se retiró el 16 de septiembre de 2026: era el campo más inerte del archivo, nada
    # lo validaba ni lo leía. Su uso previsto, declarar lo que no es portable, se deriva del artefacto.
    # Desde entonces el esquema no admite NINGUNA clave desconocida, ni siquiera esa.
    bad = {**complete_governance, "x_extensions": {"copilot": {"hooks": ["userPromptSubmitted"]}}}
    assert any("x_extensions" in e for e in errors_of(governance_validator, bad))
