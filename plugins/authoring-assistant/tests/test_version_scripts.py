"""Los dos puntos de entrada de la versión: documento en la salida estándar y nada escrito de más.

El proveedor de lanzamientos de verdad necesita red, así que aquí se comprueba lo que no depende de
él: la forma del documento, los códigos de salida y que calcular no escribe. La aritmética de la
versión y la elección del nivel ya están probadas con datos y con un doble.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from repos import PUBLISHED_SKILL, UNIT, git, make_repository, reset

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "author-unit" / "scripts"
EXIT_CLASSIFIED = 0
EXIT_COULD_NOT_RUN = 2


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return make_repository(tmp_path_factory.mktemp("scripts-version"))


@pytest.fixture(autouse=True)
def _en_una_rama_de_trabajo(repo):
    reset(repo)
    git(repo, "switch", "-q", "-c", f"fix/{UNIT}")
    yield
    reset(repo)


def run_script(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        check=False,
    )


def test_sin_cambios_el_documento_dice_que_no_hay_nada_que_versionar(repo):
    resultado = run_script("diff_classify.py", UNIT, cwd=repo)
    assert resultado.returncode == EXIT_CLASSIFIED
    documento = json.loads(resultado.stdout)
    assert documento["state"] == "empty" and "minimum" not in documento


def test_el_documento_lleva_el_minimo_y_los_motivos_con_su_ruta(repo):
    (_unit_root(repo) / "skills" / PUBLISHED_SKILL / "SKILL.md").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "se retira el skill")
    documento = json.loads(run_script("diff_classify.py", UNIT, cwd=repo).stdout)
    assert documento["minimum"] == "major"
    assert documento["reasons"][0]["path"].startswith("skills/")


def test_una_unidad_que_no_existe_es_un_fallo_de_ejecucion_no_una_clasificacion(repo):
    resultado = run_script("diff_classify.py", "unidad-que-no-existe", cwd=repo)
    assert resultado.returncode == EXIT_COULD_NOT_RUN
    assert "unidad-que-no-existe" in resultado.stderr


def test_sin_el_nombre_de_la_unidad_se_dice_el_uso(repo):
    for script in ("diff_classify.py", "version_bump.py"):
        resultado = run_script(script, cwd=repo)
        assert resultado.returncode == EXIT_COULD_NOT_RUN and "uso:" in resultado.stderr, script


def test_la_salida_estandar_lleva_solo_el_documento(repo):
    resultado = run_script("diff_classify.py", UNIT, cwd=repo)
    assert json.loads(resultado.stdout)["state"] == "empty"
    assert resultado.stderr == ""


def test_un_nivel_desconocido_se_rechaza_sin_tocar_el_manifiesto(repo):
    antes = (_unit_root(repo) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    resultado = run_script("version_bump.py", UNIT, "--apply", "gigante", cwd=repo)
    assert resultado.returncode == EXIT_COULD_NOT_RUN and "gigante" in resultado.stderr
    assert (_unit_root(repo) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8") == antes


def test_un_argumento_no_reconocido_se_dice_en_vez_de_ignorarse(repo):
    # Ignorarlo dejaria al autor creyendo que pidio algo que nadie hizo.
    resultado = run_script("version_bump.py", UNIT, "--apply-now", "major", cwd=repo)
    assert resultado.returncode == EXIT_COULD_NOT_RUN and "uso:" in resultado.stderr


def _unit_root(repo: Path) -> Path:
    return repo / "plugins" / UNIT
