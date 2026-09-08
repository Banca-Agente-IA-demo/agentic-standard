"""El asistente no toca el trabajo de nadie: las reglas, con datos y sin repositorio (T1)."""

from __future__ import annotations

import pytest

from authoring_core.domain.git_state import (
    STATE_BLOCKED,
    STATE_DIRTY,
    STATE_MAIN_CLEAN,
    STATE_UNIT_NOT_FOUND,
    STATE_UNKNOWN_BRANCH,
    STATE_WORK_BRANCH_CLEAN,
    Action,
    Observation,
    classify,
    parse_branch,
)

UNITS = ("demo-unidad", "otra-unidad")


def _observe(**overrides) -> Observation:
    return Observation(**{"branch": "main", "is_dirty": False, "units": UNITS, **overrides})


def test_en_la_rama_principal_y_sin_cambios_se_puede_seguir():
    estado = classify(_observe())
    assert estado.state == STATE_MAIN_CLEAN and estado.can_continue
    assert estado.units == UNITS


def test_en_una_rama_de_trabajo_limpia_se_retoma_leyendo_su_nombre():
    estado = classify(_observe(branch="fix/demo-unidad"))
    assert estado.state == STATE_WORK_BRANCH_CLEAN
    assert estado.action is Action.MODIFY and estado.unit == "demo-unidad"


def test_cada_prefijo_valido_declara_su_accion():
    for prefijo, accion in (("feat", Action.CREATE), ("fix", Action.MODIFY), ("deprecate", Action.DEPRECATE)):
        estado = classify(_observe(branch=f"{prefijo}/demo-unidad"))
        assert estado.action is accion, prefijo


def test_cambios_sin_guardar_detienen_en_cualquier_rama():
    # El asistente es de autoría, no de git: no guarda ni descarta nada del autor.
    for rama in ("main", "fix/demo-unidad", "otra-cosa"):
        estado = classify(_observe(branch=rama, is_dirty=True))
        assert estado.state == STATE_DIRTY and not estado.can_continue, rama
        assert "git stash" in estado.message


def test_al_detenerse_por_cambios_en_una_rama_de_trabajo_se_avisa_de_que_retomara():
    estado = classify(_observe(branch="fix/demo-unidad", is_dirty=True))
    assert "retomará esa unidad" in estado.message


def test_una_rama_que_no_sigue_la_forma_esperada_detiene_y_dice_como_salir():
    estado = classify(_observe(branch="mi-rama-cualquiera"))
    assert estado.state == STATE_UNKNOWN_BRANCH
    assert "git switch main" in estado.message and "git branch -m" in estado.message


@pytest.mark.parametrize("rama", ["Feat/Unidad", "fix/-empieza-mal", "fix/con/dos-barras", "fix/", "fix"])
def test_un_nombre_de_rama_mal_formado_no_se_interpreta(rama: str):
    assert parse_branch(rama) is None


def test_una_rama_de_modificacion_sobre_una_unidad_inexistente_se_rechaza():
    estado = classify(_observe(branch="fix/no-existe"))
    assert estado.state == STATE_UNIT_NOT_FOUND
    assert "demo-unidad" in estado.message


def test_una_rama_de_creacion_admite_una_unidad_que_todavia_no_existe():
    # Es la que se está creando: exigir que exista haría imposible crear nada.
    estado = classify(_observe(branch="feat/unidad-nueva"))
    assert estado.state == STATE_WORK_BRANCH_CLEAN and estado.unit == "unidad-nueva"


def test_una_rama_de_obsolescencia_sobre_una_unidad_inexistente_se_rechaza():
    assert classify(_observe(branch="deprecate/no-existe")).state == STATE_UNIT_NOT_FOUND


@pytest.mark.parametrize(
    "razon", ["merge a medias", "rebase a medias", "HEAD suelto (detached)", "sin remoto origin"]
)
def test_cada_estado_irresoluble_bloquea_y_dice_cual_es(razon: str):
    estado = classify(_observe(blocked_reason=razon))
    assert estado.state == STATE_BLOCKED and razon in estado.message


def test_lo_que_bloquea_manda_sobre_todo_lo_demas():
    # Con el repositorio a medias no tiene sentido hablar de ramas ni de cambios sin guardar.
    estado = classify(_observe(branch="fix/demo-unidad", is_dirty=True, blocked_reason="merge a medias"))
    assert estado.state == STATE_BLOCKED


def test_la_rama_principal_atrasada_avisa_y_no_detiene():
    # El asistente parte del origen, y el autor debe saberlo.
    estado = classify(_observe(behind_remote=True))
    assert estado.state == STATE_MAIN_CLEAN and estado.behind_remote


def test_una_rama_de_trabajo_atrasada_avisa_y_no_detiene():
    # Reordenar el historial es del autor: el asistente no rebasa nada.
    estado = classify(_observe(branch="fix/demo-unidad", behind_main=True))
    assert estado.state == STATE_WORK_BRANCH_CLEAN and estado.behind_main


def test_un_manifiesto_ilegible_consta_en_todos_los_estados():
    # Ignorarlo en silencio haría que su unidad faltara de la lista y el asistente dijera que no
    # existe, que es el peor mensaje posible.
    ilegibles = ("plugins/rota/.claude-plugin/plugin.json",)
    for rama in ("main", "fix/demo-unidad", "otra-cosa"):
        estado = classify(_observe(branch=rama, unreadable_manifests=ilegibles))
        assert estado.unreadable_manifests == ilegibles, rama
