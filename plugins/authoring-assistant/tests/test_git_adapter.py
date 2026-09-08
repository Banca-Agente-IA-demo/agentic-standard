"""Los seis escenarios del banco de pruebas, contra repositorios de verdad y sin red.

Es el criterio de cierre del hito: el estado clasificado tiene que ser el esperado en los seis, y el
asistente no puede haber escrito nada al averiguarlo.
"""

from __future__ import annotations

import json

import pytest

from authoring_core.adapters.git import GitUnavailable, observe, run_git
from authoring_core.application.author_context import read_git_state
from authoring_core.domain.git_state import STATE_MAIN_CLEAN, STATE_WORK_BRANCH_CLEAN, Action

from repos import SCENARIOS, UNIT, apply_scenario, git, make_repository, reset


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    """Un solo repositorio para todo el módulo; cada prueba lo devuelve a su punto de partida."""
    return make_repository(tmp_path_factory.mktemp("banco"))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_cada_escenario_del_banco_de_pruebas_da_su_estado(repo, scenario):
    apply_scenario(repo, scenario)
    assert read_git_state(repo).state == scenario


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_clasificar_no_escribe_nada_en_el_repositorio(repo, scenario):
    # El asistente es de autoría, no de git: clasificar es leer.
    apply_scenario(repo, scenario)
    antes = git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD")
    read_git_state(repo)
    assert (git(repo, "status", "--porcelain"), git(repo, "rev-parse", "HEAD")) == antes


def test_la_unidad_del_repositorio_se_encuentra_por_su_manifiesto(repo):
    apply_scenario(repo, "main_clean")
    assert observe(repo).units == (UNIT,)


def test_al_retomar_se_leen_la_accion_y_la_unidad_del_nombre_de_la_rama(repo):
    apply_scenario(repo, "work_branch_clean")
    estado = read_git_state(repo)
    assert estado.state == STATE_WORK_BRANCH_CLEAN
    assert estado.action is Action.MODIFY and estado.unit == UNIT


def test_un_manifiesto_ilegible_consta_y_su_unidad_no_aparece(repo):
    apply_scenario(repo, "main_clean")
    rota = repo / "plugins" / "rota" / ".claude-plugin"
    rota.mkdir(parents=True)
    (rota / "plugin.json").write_text("{ esto no es json", encoding="utf-8")
    try:
        observado = observe(repo)
        assert observado.units == (UNIT,)
        assert observado.unreadable_manifests == ("plugins/rota/.claude-plugin/plugin.json",)
    finally:
        reset(repo)


def test_un_manifiesto_sin_nombre_tambien_consta(repo):
    apply_scenario(repo, "main_clean")
    sin_nombre = repo / "plugins" / "sin-nombre" / ".claude-plugin"
    sin_nombre.mkdir(parents=True)
    (sin_nombre / "plugin.json").write_text(json.dumps({"version": "1.0.0"}), encoding="utf-8")
    try:
        assert observe(repo).unreadable_manifests == ("plugins/sin-nombre/.claude-plugin/plugin.json",)
    finally:
        reset(repo)


def test_la_rama_principal_atrasada_respecto_al_origen_se_avisa(repo):
    # El asistente parte del origen; si el autor no lo sabe, no entiende de dónde sale su rama.
    apply_scenario(repo, "main_clean")
    (repo / "NUEVO.md").write_text("avance\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "avance que va al origen")
    git(repo, "push", "-q", "origin", "main")
    try:
        git(repo, "reset", "-q", "--hard", "HEAD~1")  # la copia local se queda atrás
        estado = read_git_state(repo)
        assert estado.state == STATE_MAIN_CLEAN and estado.behind_remote
    finally:
        git(repo, "push", "-q", "-f", "origin", "main")
        reset(repo)


def test_una_rama_de_trabajo_atrasada_respecto_a_la_principal_se_avisa(repo):
    apply_scenario(repo, "work_branch_clean")
    git(repo, "switch", "-q", "main")
    (repo / "NUEVO.md").write_text("avance en main\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "avance")
    git(repo, "switch", "-q", f"fix/{UNIT}")
    try:
        estado = read_git_state(repo)
        assert estado.state == STATE_WORK_BRANCH_CLEAN and estado.behind_main
    finally:
        reset(repo)


def test_cuando_no_se_puede_preguntar_a_git_se_dice_en_vez_de_clasificar(repo):
    """No poder preguntar no es un estado del repositorio.

    Este caso no se prueba con una carpeta fuera de todo repositorio: en esta máquina el directorio
    personal **es** un repositorio, así que el temporal cae dentro y git responde. Es un aviso para
    quien lea esto: `rev-parse --show-toplevel` puede resolver a un repositorio que no es el del autor.
    """
    with pytest.raises(GitUnavailable):
        run_git(["subcomando-que-no-existe"], repo)
