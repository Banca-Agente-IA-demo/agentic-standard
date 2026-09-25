"""La ficha se crea con los campos que el blueprint exige, y un nombre tomado no la sobrescribe.

El cliente se inyecta como doble, así que ninguna prueba toca la red. Es lo que PR6 pide: el
cableado está en la firma y no escondido dentro de la función.
"""

from __future__ import annotations

import pytest

from port_catalog.errors import CatalogUnavailableError, UnitAlreadyRegisteredError
from port_catalog.unit_entity import INITIAL_STATE, register_unit, unregister_unit

# Los seis campos que el blueprint `agentic_unit` declara obligatorios.
REQUIRED_PROPERTIES = ("state", "form", "owner_team", "repo", "path", "sha")

UNIT = {
    "name": "cnf-migration-flow",
    "form": "grouped",
    "owner_team": "squad-cnf-migration",
    "owner_contact": "squad-cnf-migration@bcp.com.pe",
    "risk_level": "medium",
    "repository": "Banca-Agente-IA-demo/agents-modernization",
    "path": "plugins/cnf-migration-flow",
    "sha": "0123456789abcdef0123456789abcdef01234567",
    "mcp_servers": (),
}


class FakeClient:
    """Recuerda lo que se le pidió y devuelve lo que la prueba le diga que devuelva."""

    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self._error = error

    def post(self, path: str, body: dict) -> dict:
        self.calls.append(("POST", path, body))
        if self._error:
            raise self._error
        return {"ok": True}

    def delete(self, path: str) -> dict:
        self.calls.append(("DELETE", path, None))
        if self._error:
            raise self._error
        return {"ok": True}


def test_la_ficha_nace_con_los_seis_campos_que_el_blueprint_exige() -> None:
    client = FakeClient()
    register_unit(client, **UNIT)
    properties = client.calls[0][2]["properties"]
    for field in REQUIRED_PROPERTIES:
        assert properties.get(field), field


def test_la_unidad_nace_en_desarrollo_y_ese_estado_no_se_teclea() -> None:
    # Una unidad con ficha y sin ningún release está en Desarrollo. Ninguna otra transición pasa por
    # aquí: las demás las deriva la automatización de los hechos del release.
    client = FakeClient()
    register_unit(client, **UNIT)
    assert client.calls[0][2]["properties"]["state"] == INITIAL_STATE == "desarrollo"


def test_el_identificador_de_la_ficha_es_el_nombre_de_la_unidad() -> None:
    # Es lo que hace que la comprobación de unicidad pueda preguntar por la entidad directamente, sin
    # recorrer el catálogo entero.
    client = FakeClient()
    register_unit(client, **UNIT)
    assert client.calls[0][2]["identifier"] == "cnf-migration-flow"


def test_se_crea_y_no_se_actualiza() -> None:
    # Actualizar convertiría un choque de nombres en el borrado silencioso de la ficha ajena.
    client = FakeClient()
    register_unit(client, **UNIT)
    method, path, _ = client.calls[0]
    assert method == "POST"
    assert "upsert" not in path


def test_un_nombre_ya_tomado_es_una_respuesta_y_no_una_averia() -> None:
    # Medido el 25 de septiembre de 2026: Port devuelve 409 identifier_taken. El motivo que sale de
    # aquí es el que la persona lee en la pantalla del formulario, así que nombra la unidad y dice
    # qué hacer.
    client = FakeClient(CatalogUnavailableError(
        'POST /blueprints/agentic_unit/entities -> 409: {"error":"identifier_taken"}'))
    with pytest.raises(UnitAlreadyRegisteredError, match="cnf-migration-flow"):
        register_unit(client, **UNIT)


def test_cualquier_otro_fallo_del_catalogo_burbujea_sin_disfrazarse() -> None:
    # Un 500 no es un nombre ocupado, y decirle a la persona que elija otro nombre la mandaría a
    # corregir algo que estaba bien.
    client = FakeClient(CatalogUnavailableError("POST ... -> 500: algo se rompio"))
    with pytest.raises(CatalogUnavailableError):
        register_unit(client, **UNIT)


def test_retirar_una_ficha_que_no_se_puede_borrar_no_tapa_el_fallo_original() -> None:
    # La compensación avisa y sigue: quien lea el registro necesita ver el fallo que la provocó y el
    # de la propia compensación, no solo el segundo.
    client = FakeClient(CatalogUnavailableError("DELETE ... -> 500"))
    unregister_unit(client, "cnf-migration-flow")
    assert client.calls[0][0] == "DELETE"
