"""Cada artefacto tiene su ficha, cualificada por su unidad y relacionada con ella.

El cliente se inyecta como doble, así que ninguna prueba toca la red.
"""

from __future__ import annotations

from port_catalog.artifact_entity import (artifact_identifier, register_artifacts,
                                          unregister_artifacts)
from port_catalog.errors import CatalogUnavailableError

ARTIFACTS = (
    ("skill", "atlas-to-cnf-vault", "skills/atlas-to-cnf-vault/SKILL.md"),
    ("agent", "atla.cnf-migrator.analyst", "agents/atla.cnf-migrator.analyst.agent.md"),
)


class FakeClient:
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


def test_se_crea_una_ficha_por_artefacto_y_ni_una_mas() -> None:
    client = FakeClient()
    register_artifacts(client, "cnf-migration-flow", ARTIFACTS)
    assert len(client.calls) == len(ARTIFACTS), [c[2]["identifier"] for c in client.calls]


def test_el_identificador_cualifica_el_artefacto_con_su_unidad() -> None:
    # Dos unidades pueden contener un artefacto con el mismo nombre, así que el nombre suelto no
    # basta como identidad en el catálogo.
    assert artifact_identifier("cnf-migration-flow", "atlas-to-cnf-vault") == (
        "cnf-migration-flow--atlas-to-cnf-vault")


def test_el_separador_es_doble_para_que_el_nombre_pueda_llevar_guiones() -> None:
    # Con un separador de un guion, `a-b--c` y `a--b-c` serían el mismo texto y la identidad dejaría
    # de ser reversible.
    assert artifact_identifier("a-b", "c") != artifact_identifier("a", "b-c")


def test_cada_ficha_apunta_a_su_unidad() -> None:
    # La relación es obligatoria en el blueprint: un artefacto sin unidad no tiene dueño ni estado.
    client = FakeClient()
    register_artifacts(client, "cnf-migration-flow", ARTIFACTS)
    for _, _, body in client.calls:
        assert body["relations"]["unit"] == "cnf-migration-flow"


def test_la_ficha_no_escribe_el_estado_porque_lo_espeja() -> None:
    # El artefacto no puede estar en un estado distinto al de su unidad, así que no se escribe dos
    # veces: se refleja por la relación.
    client = FakeClient()
    register_artifacts(client, "cnf-migration-flow", ARTIFACTS)
    for _, _, body in client.calls:
        assert "state" not in body["properties"]


def test_las_suites_sembradas_no_cuentan_como_evals() -> None:
    # El esqueleto siembra el archivo, pero lleno de marcadores. Decir que tiene suite sería la
    # misma clase de mentira que una descripción plausible en un artefacto sin terminar.
    client = FakeClient()
    register_artifacts(client, "cnf-migration-flow", ARTIFACTS)
    for _, _, body in client.calls:
        assert body["properties"]["has_evals"] is False


def test_retirar_una_ficha_que_falla_no_detiene_a_las_demas() -> None:
    # La compensación tiene que intentarlo con todas: parar en la primera dejaría a medias justo lo
    # que existe para no dejar nada a medias.
    client = FakeClient(CatalogUnavailableError("DELETE ... -> 500"))
    unregister_artifacts(client, "cnf-migration-flow", ("uno", "dos", "tres"))
    assert len(client.calls) == 3
