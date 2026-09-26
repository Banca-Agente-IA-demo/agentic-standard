"""El paso de creación de punta a punta, con el catálogo sustituido por un doble.

El doble se inyecta por argumento y no con `monkeypatch` (PR6): `create_unit` recibe el cliente en
la firma precisamente para que esto sea posible sin parchear módulos.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from create_unit.commons.enums.validation_status import ValidationStatus
from create_unit.create_unit import create_unit

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"

# El formulario tal y como lo envía Port, con los campos numerados sin colapsar y los dos campos de
# entidad como objeto entero: es la forma medida el 25 de septiembre de 2026, no una simplificación.
PORT_FORM = {
    "name": "probe-unidad",
    "description": "Unidad de prueba del paso de creacion.",
    "owner_team": {"identifier": "19716830", "title": "squad-cnf-runtime",
                   "properties": {"slug": "squad-cnf-runtime"}},
    "team_mailbox": "squad-cnf-runtime@bcp.com.pe",
    "risk_level": "medium",
    "unit_form": "grouped",
    "skill_1": "probe-rest",
    "agent_1": "atla.probe.analyst",
    "repository": {"identifier": "Banca-Agente-IA-demo/agents-modernization"},
}

OCCUPIED_NAMES = ("spring-to-quarkus", "otra-unidad")


class FakeCatalog:
    """Un catálogo que contesta lo que se le diga y cuenta cuántas veces le preguntaron."""

    def __init__(self, names: tuple[str, ...]) -> None:
        self._names = names
        self.calls: list[str] = []

    def get(self, path: str) -> dict:
        self.calls.append(path)
        return {"entities": [{"identifier": name} for name in self._names]}


def _write_form(directory: Path, form: dict) -> Path:
    payload_file = directory / "payload.json"
    payload_file.write_text(json.dumps(form), encoding="utf-8")
    return payload_file


def test_el_formulario_valido_siembra_el_esqueleto_y_devuelve_valid(tmp_path) -> None:
    outcome = create_unit(_write_form(tmp_path, PORT_FORM), TEMPLATES, tmp_path / "root",
                          FakeCatalog(OCCUPIED_NAMES), "")

    assert outcome.status is ValidationStatus.VALID, (
        "el formulario es correcto y el nombre esta libre, asi que el veredicto tenia que ser "
        "valid; salio %s con motivo %r" % (outcome.status, outcome.reason))
    assert outcome.files, "se dio por valido y no escribio ningun archivo: el esqueleto falta"
    assert outcome.reason == "", "un veredicto valid no tiene motivo que mostrarle a nadie"


def test_el_nombre_ya_ocupado_no_escribe_nada_en_disco(tmp_path) -> None:
    root = tmp_path / "root"
    outcome = create_unit(_write_form(tmp_path, PORT_FORM), TEMPLATES, root,
                          FakeCatalog(("probe-unidad",) + OCCUPIED_NAMES), "")

    assert outcome.status is ValidationStatus.NAME_TAKEN
    assert outcome.files == (), (
        "sembro con el nombre ya ocupado. La rama y la ficha tienen que existir las dos o ninguna, "
        "y un esqueleto escrito aqui deja media unidad")
    assert not root.exists() or not any(root.rglob("*")), (
        "quedaron archivos bajo la raiz de trabajo pese a no haber sembrado")


def test_el_formulario_mal_formado_no_gasta_una_llamada_al_catalogo(tmp_path) -> None:
    catalog = FakeCatalog(OCCUPIED_NAMES)
    outcome = create_unit(_write_form(tmp_path, {"name": "MAL NOMBRE"}), TEMPLATES,
                          tmp_path / "root", catalog, "")

    assert outcome.status is ValidationStatus.MALFORMED_PAYLOAD
    assert catalog.calls == [], (
        "pregunto al catalogo con un formulario que ya se sabia invalido: son %s. Un formulario mal "
        "formado no debe gastar ni una llamada ni un token" % catalog.calls)


def test_el_motivo_del_formulario_mal_formado_nombra_el_campo_que_fallo(tmp_path) -> None:
    outcome = create_unit(_write_form(tmp_path, {"name": "MAL NOMBRE"}), TEMPLATES,
                          tmp_path / "root", FakeCatalog(()), "")

    assert "name" in outcome.reason, (
        "el motivo no nombra el campo que la persona escribio mal, asi que no puede corregirlo: %r"
        % outcome.reason)


def test_el_equipo_dueno_llega_al_payload_normalizado_como_slug_y_no_como_numero(tmp_path) -> None:
    """Medido el 25 de septiembre de 2026: Port envia la entidad entera, no el identificador."""
    outcome = create_unit(_write_form(tmp_path, PORT_FORM), TEMPLATES, tmp_path / "root",
                          FakeCatalog(OCCUPIED_NAMES), "")

    normalized = json.loads(outcome.normalized_payload)
    assert normalized["owner_team"] == "squad-cnf-runtime", (
        "el equipo quedo como %r. Un manifiesto que declare el id numerico no sirve para avisar a "
        "nadie, que es para lo que existe ese campo" % normalized["owner_team"])


def test_los_campos_numerados_del_formulario_llegan_colapsados_en_listas(tmp_path) -> None:
    outcome = create_unit(_write_form(tmp_path, PORT_FORM), TEMPLATES, tmp_path / "root",
                          FakeCatalog(OCCUPIED_NAMES), "")

    normalized = json.loads(outcome.normalized_payload)
    for field, expected in (("skills", ["probe-rest"]), ("agents", ["atla.probe.analyst"])):
        assert normalized[field] == expected, (
            "el campo %s llego como %r en vez de %r: el job que registra la ficha lo lee de aqui"
            % (field, normalized[field], expected))


def test_el_veredicto_tiene_las_mismas_claves_valga_lo_que_valga_el_estado(tmp_path) -> None:
    """La acción emite cuatro outputs sin mirar el estado: si el veredicto cambiara de forma, el
    `python - "$VERDICT"` del YAML reventaria con un KeyError en el desenlace que no se probo."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    valido = create_unit(_write_form(tmp_path / "a", PORT_FORM), TEMPLATES, tmp_path / "root-a",
                         FakeCatalog(OCCUPIED_NAMES), "")
    invalido = create_unit(_write_form(tmp_path / "b", {"name": "MAL"}), TEMPLATES,
                           tmp_path / "root-b", FakeCatalog(()), "")

    assert dataclasses.asdict(valido).keys() == dataclasses.asdict(invalido).keys(), (
        "el veredicto cambia de forma segun el resultado, asi que quien lo lee tiene que mirar "
        "primero el estado para saber que campos existen")
    assert set(dataclasses.asdict(valido)) == {"status", "reason", "unit_name",
                                               "normalized_payload", "files"}, (
        "cambiaron las claves del veredicto sin tocar la action, que las emite una a una")
