"""Cruza lo que el contrato declara con lo que la action y el workflow implementan, sin ejecutar nada.

Es C5 aplicado a este paso: la información de qué sale y quién lo lee estaba escrita en tres sitios
(el contrato, los outputs de la action y los `if:` del workflow) y nada garantizaba que dijeran lo
mismo. Esta prueba es lo que lo garantiza.

Y es PR4: el cruce podría vivir en un comando, pero un desarrollador no ejecuta un comando que no
conoce, y sí ejecuta la suite antes de empujar.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import yaml

from create_unit.commons.enums.validation_status import ValidationStatus
from create_unit.commons.models.seams import CreationOutcome
from create_unit.contract import CREATE_UNIT_CONTRACT

REPO = Path(__file__).resolve().parents[2]
ACTION = REPO / ".github" / "actions" / "create-unit" / "action.yml"
WORKFLOW = REPO / ".github" / "workflows" / "create-unit.yml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_la_action_emite_exactamente_las_claves_que_el_contrato_declara() -> None:
    declared = {key.name for key in CREATE_UNIT_CONTRACT.outputs}
    implemented = set(_load(ACTION)["outputs"])

    assert declared == implemented, (
        "el contrato declara %s y la action emite %s. La clave que sobra no la lee nadie (C6) y la "
        "que falta la lee alguien que se encontrara una cadena vacia"
        % (sorted(declared), sorted(implemented)))


def test_cada_clave_declarada_dice_quien_la_lee() -> None:
    keys = CREATE_UNIT_CONTRACT.outputs
    assert len(keys) == len(_load(ACTION)["outputs"]), "el recorrido dejo de mirar alguna clave"
    for key in keys:
        assert key.source.strip(), (
            "la clave %s no declara quien la lee. Sin ese dato no tiene justificacion para estar "
            "declarada: un contrato es la interseccion de lo que se promete con lo que alguien "
            "consume (C6)" % key.name)


def test_el_workflow_enruta_por_el_valor_del_enumerado_y_no_por_un_booleano() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    valid = ValidationStatus.VALID.value

    assert "validation-status == '%s'" % valid in workflow, (
        "los steps que escriben no condicionan por `validation-status == '%s'`. Si condicionan por "
        "otra cosa, el enumerado no gobierna el enrutado y el veredicto vuelve a ser prosa" % valid)


def test_el_workflow_tiene_un_solo_job_con_el_permiso_de_escritura() -> None:
    """El diagrama de autoria dibuja un job. La consecuencia esta escrita en la cabecera del
    workflow: el step que procesa el formulario comparte token con el que empuja."""
    jobs = _load(WORKFLOW)["jobs"]

    assert list(jobs) == ["create-unit"], (
        "el workflow tiene los jobs %s. El diseno fija uno solo, como el diagrama de autoria: "
        "partirlo en dos vuelve a la forma que esta convergencia retiro" % sorted(jobs))
    assert jobs["create-unit"]["permissions"] == {"contents": "write"}, (
        "el job no declara exactamente `contents: write`. El permiso se concede por job y no se "
        "puede afinar por step, asi que declarar de mas expone de mas")


def test_el_esqueleto_no_viaja_como_artifact() -> None:
    """Con un solo job no hay frontera que cruzar: el esqueleto se compone sobre el arbol clonado
    y se empuja desde ahi. Subirlo y bajarlo seria un rodeo sin destinatario."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for accion in ("upload-artifact", "download-artifact"):
        assert accion not in workflow, (
            "el workflow usa `%s`. Eso existia para pasar el esqueleto entre dos jobs, y ya no hay "
            "dos jobs" % accion)


def test_la_action_no_lleva_python_incrustado() -> None:
    """Un heredoc de Python dentro del YAML es codigo sin archivo, sin pruebas y sin revision. Los
    outputs y el resumen los escribe el adaptador, que si esta en un archivo (AGENTS.md E1)."""
    action = ACTION.read_text(encoding="utf-8")
    for marca in ("<<'PY'", 'python - "', "python -c"):
        assert marca not in action, (
            "la action vuelve a incrustar Python en el shell (%s). Lo que decida o formatee algo va "
            "a un archivo del paquete o al adaptador" % marca)


def test_el_adaptador_emite_los_outputs_que_la_action_declara() -> None:
    """La traduccion del veredicto a outputs del step la hace el adaptador; la action solo los
    declara. Una clave escrita en un lado y no en el otro deja al consumidor una cadena vacia, que
    es el fallo peor: no revienta, enruta mal."""
    adapter = (REPO / "tools" / "create_unit_cli.py").read_text(encoding="utf-8")
    written = set(re.findall(r'f"(\w+)=', adapter))

    assert written, "el adaptador ya no emite outputs por clave: revisa si esta prueba sigue mirando"

    declarados = {name.replace("-", "_") for name in _load(ACTION)["outputs"]}
    assert written == declarados, (
        "el adaptador escribe %s y la action declara %s. El que sobre no lo lee nadie (C6) y el que "
        "falte llega vacio" % (sorted(written), sorted(declarados)))


def test_el_veredicto_no_pierde_campos_por_el_camino() -> None:
    """Los campos del sello que NO salen como output son una decision, no un olvido: `files` es para
    el resumen del job, que lo lee una persona, y no para enrutar."""
    campos = {field.name for field in dataclasses.fields(CreationOutcome)}
    declarados = {name.replace("-", "_") for name in _load(ACTION)["outputs"]}
    solo_para_la_persona = {"files", "status"}

    assert campos - declarados == solo_para_la_persona, (
        "los campos que no salen como output son %s y se esperaban %s. Si aparece uno nuevo, di por "
        "que no lo lee nadie o emitelo"
        % (sorted(campos - declarados), sorted(solo_para_la_persona)))


def test_el_estandar_no_se_clona_en_ningun_sitio() -> None:
    """Medido en la ronda 29: `checkout` del estandar privado falla con `Repository not found`."""
    for path in (WORKFLOW, ACTION):
        text = path.read_text(encoding="utf-8")
        for forbidden in ("git clone", "repository: Banca-Agente-IA-demo/agentic-standard"):
            assert forbidden not in text, (
                "%s intenta traerse el estandar con %r. No funciona con el token por defecto: el "
                "codigo llega dentro de la composite action, por su arbol" % (path.name, forbidden))
