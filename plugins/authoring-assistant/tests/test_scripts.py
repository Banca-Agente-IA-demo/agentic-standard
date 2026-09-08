"""Lo que el modelo consume de verdad: un documento en la salida estándar y el código de salida.

Los prototipos del banco de pruebas incumplían las dos reglas del plan: imprimían el error en la
salida estándar y salían con fallo al detenerse. Estas pruebas fijan lo corregido (T3).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from repos import SCENARIOS, UNIT, apply_scenario, make_repository, reset

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "author-unit" / "scripts"
EXIT_CLASSIFIED = 0
EXIT_COULD_NOT_RUN = 2


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return make_repository(tmp_path_factory.mktemp("scripts"))


def run_script(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        check=False,
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_detenerse_no_es_fallar(repo, scenario):
    # Un estado de parada es un resultado. Sólo no poder ejecutar es un fallo.
    apply_scenario(repo, scenario)
    resultado = run_script("git_state.py", cwd=repo)
    assert resultado.returncode == EXIT_CLASSIFIED, resultado.stderr
    assert json.loads(resultado.stdout)["state"] == scenario


def test_la_salida_estandar_lleva_solo_el_documento(repo):
    apply_scenario(repo, "main_clean")
    resultado = run_script("git_state.py", cwd=repo)
    assert json.loads(resultado.stdout)["state"] == "main_clean"
    assert resultado.stderr == ""


def test_el_diagnostico_va_a_la_salida_de_error_y_no_al_documento(repo):
    # Con un comando desconocido el script no puede clasificar: eso sí es un fallo.
    apply_scenario(repo, "main_clean")
    resultado = run_script("intent.py", "inventado", cwd=repo)
    assert resultado.returncode == EXIT_COULD_NOT_RUN
    assert "inventado" in resultado.stderr
    assert json.loads(resultado.stdout)["state"] == "unavailable"


def test_el_documento_no_lleva_campos_vacios(repo):
    # El modelo lee campos; un campo nulo invita a interpretarlo.
    apply_scenario(repo, "main_clean")
    documento = json.loads(run_script("git_state.py", cwd=repo).stdout)
    assert all(valor not in (None, [], ()) for valor in documento.values()), documento


def test_al_retomar_el_documento_trae_la_accion_y_la_unidad(repo):
    apply_scenario(repo, "work_branch_clean")
    documento = json.loads(run_script("git_state.py", cwd=repo).stdout)
    assert documento["action"] == "fix" and documento["unit"] == UNIT


def test_la_intencion_se_guarda_lee_y_borra_desde_la_linea_de_ordenes(repo):
    apply_scenario(repo, "main_clean")
    try:
        guardado = json.loads(run_script("intent.py", "set", "fix", UNIT, cwd=repo).stdout)
        assert guardado == {"pending": True, "action": "fix", "unit": UNIT}
        assert json.loads(run_script("intent.py", cwd=repo).stdout) == guardado
        assert json.loads(run_script("intent.py", "clear", cwd=repo).stdout) == {"pending": False}
    finally:
        reset(repo)


def test_guardar_sin_decir_la_accion_es_un_fallo_de_uso(repo):
    apply_scenario(repo, "main_clean")
    resultado = run_script("intent.py", "set", cwd=repo)
    assert resultado.returncode == EXIT_COULD_NOT_RUN and "uso:" in resultado.stderr


def test_la_comprobacion_de_herramientas_dice_cual_falta_en_vez_de_fallar(repo):
    # La prueba no puede dar por hecho qué hay instalado: en el runner de CI falta la herramienta de
    # GitHub y la primera versión de esta prueba, escrita contra la máquina del autor, se cayó allí.
    # Lo que sí es del código: clasifica siempre, y cuando algo falta lo nombra.
    apply_scenario(repo, "main_clean")
    resultado = run_script("preflight.py", cwd=repo)
    assert resultado.returncode == EXIT_CLASSIFIED
    documento = json.loads(resultado.stdout)
    assert documento["state"] in ("ok", "missing_tool")
    if documento["state"] == "missing_tool":
        assert documento["missing"], documento


def test_los_scripts_funcionan_sin_instalar_nada(repo):
    # Se ejecutan con el intérprete del sistema, sin entorno ni paquete instalado: es la promesa que
    # se le hace al autor.
    apply_scenario(repo, "main_clean")
    for script in ("preflight.py", "git_state.py", "intent.py"):
        assert run_script(script, cwd=repo).returncode == EXIT_CLASSIFIED, script


def test_el_estado_se_lee_del_repositorio_desde_el_que_se_invoca(repo):
    # El script se ejecuta desde la carpeta del autor, no desde la del plugin.
    apply_scenario(repo, "unknown_branch")
    assert json.loads(run_script("git_state.py", cwd=repo).stdout)["state"] == "unknown_branch"
