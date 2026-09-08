"""La intención sobrevive a cerrar la sesión, y no ensucia ni viaja.

Es lo que hace que detenerse no cueste el trabajo hecho hasta ahí.
"""

from __future__ import annotations

import subprocess

import pytest

from authoring_core.application.author_context import forget_intent, read_intent, remember_intent
from authoring_core.domain.git_state import Action

from repos import UNIT, git, make_repository, reset


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return make_repository(tmp_path_factory.mktemp("intencion"))


@pytest.fixture(autouse=True)
def _limpio(repo):
    reset(repo)
    yield
    reset(repo)


def test_sin_nada_guardado_no_hay_nada_pendiente(repo):
    assert read_intent(repo).pending is False


def test_lo_guardado_se_recupera_en_una_invocacion_posterior(repo):
    # Cada invocación es un proceso nuevo: si esto funciona, retomar funciona.
    remember_intent("fix", UNIT, repo)
    recuperado = read_intent(repo)
    assert recuperado.pending and recuperado.action is Action.MODIFY and recuperado.unit == UNIT


def test_una_accion_sin_unidad_tambien_se_recupera(repo):
    remember_intent("feat", None, repo)
    assert read_intent(repo).pending and read_intent(repo).unit is None


def test_guardar_de_nuevo_sin_unidad_borra_la_anterior(repo):
    # Si no, el autor cambiaría de idea sobre qué hacer y arrastraría la unidad de antes.
    remember_intent("fix", UNIT, repo)
    remember_intent("feat", None, repo)
    assert read_intent(repo).unit is None


def test_completar_el_trabajo_borra_lo_pendiente(repo):
    remember_intent("fix", UNIT, repo)
    assert forget_intent(repo).pending is False
    assert read_intent(repo).pending is False


def test_la_intencion_no_ensucia_el_arbol_de_trabajo(repo):
    # Vive en la configuración local, así que `git status` no la ve y nunca se versiona.
    remember_intent("deprecate", UNIT, repo)
    assert git(repo, "status", "--porcelain") == ""


def test_una_copia_nueva_del_repositorio_no_hereda_la_intencion(repo, tmp_path):
    # La memoria vive en la copia, no en el código: quien clona empieza de cero.
    remember_intent("fix", UNIT, repo)
    copia = tmp_path / "copia"
    subprocess.run(["git", "clone", "-q", str(repo), str(copia)], check=True, capture_output=True)
    assert read_intent(copia).pending is False


def test_una_accion_corrupta_guardada_a_mano_no_se_da_por_buena(repo):
    git(repo, "config", "--local", "authoring.pendingAction", "borrar-todo")
    intent = read_intent(repo)
    assert intent.pending is False and "borrar-todo" in intent.message
