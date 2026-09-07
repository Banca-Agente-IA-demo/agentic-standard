"""El adaptador que pregunta a git, contra repositorios de verdad creados en tmp_path."""

from __future__ import annotations

import subprocess

import pytest

from agentic_validator.adapters.repository import changed_paths, unit_roots

pytestmark = pytest.mark.slow


def _git(repository, *args) -> None:
    subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)


def _repository(tmp_path):
    """Un repositorio con una confirmación inicial en `main` y una unidad ya dentro."""
    root = tmp_path / "agents-demo"
    (root / "plugins" / "uno").mkdir(parents=True)
    (root / "plugins" / "uno" / "GOVERNANCE.json").write_text("{}", encoding="utf-8")
    (root / "README.md").write_text("inicial\n", encoding="utf-8")
    _git(root.parent, "init", "-q", "-b", "main", str(root))
    _git(root, "config", "user.email", "prueba@example.com")
    _git(root, "config", "user.name", "prueba")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "inicial")
    return root


def test_las_rutas_cambiadas_en_una_rama_son_las_que_esa_rama_añadio(tmp_path):
    root = _repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/algo")
    (root / "plugins" / "uno" / "SKILL.md").write_text("---\nname: uno\n---\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "añade el skill")
    resultado = changed_paths(root, "main")
    assert resultado.unavailable is None
    assert resultado.paths == ("plugins/uno/SKILL.md",)


def test_lo_que_avanza_en_la_rama_base_no_se_atribuye_al_autor(tmp_path):
    # El diff de tres puntos compara con el ancestro común: es lo que el autor entiende por «lo mío».
    root = _repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/algo")
    (root / "plugins" / "uno" / "SKILL.md").write_text("---\nname: uno\n---\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "lo mio")
    _git(root, "switch", "-q", "main")
    (root / "OTRO.md").write_text("ajeno\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ajeno")
    _git(root, "switch", "-q", "feat/algo")
    assert changed_paths(root, "main").paths == ("plugins/uno/SKILL.md",)


def test_sin_cambios_respecto_a_la_base_no_hay_rutas(tmp_path):
    root = _repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/vacia")
    assert changed_paths(root, "main").paths == ()


def test_una_referencia_que_no_existe_se_informa_como_no_disponible(tmp_path):
    # No es un error del autor: en el primer push de una rama puede no haber con qué comparar.
    root = _repository(tmp_path)
    resultado = changed_paths(root, "origin/no-existe")
    assert resultado.unavailable and resultado.paths == ()


def test_una_carpeta_que_no_es_un_repositorio_se_informa_como_no_disponible(tmp_path):
    assert changed_paths(tmp_path, "main").unavailable


def test_las_raices_de_unidad_son_las_carpetas_que_llevan_su_gobierno(tmp_path):
    root = _repository(tmp_path)
    (root / "skills" / "dos").mkdir(parents=True)
    (root / "skills" / "dos" / "GOVERNANCE.json").write_text("{}", encoding="utf-8")
    assert unit_roots(root) == ("plugins/uno", "skills/dos")


def test_el_historial_de_git_no_se_confunde_con_una_unidad(tmp_path):
    root = _repository(tmp_path)
    assert all(not raiz.startswith(".git") for raiz in unit_roots(root))
