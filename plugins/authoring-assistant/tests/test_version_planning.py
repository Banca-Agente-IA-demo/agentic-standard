"""El caso de uso completo contra un repositorio de verdad, con los lanzamientos puestos por un doble.

El proveedor de lanzamientos es lo único que necesitaría red, y llega por el puerto: por eso esta
suite corre sin salir de la máquina.
"""

from __future__ import annotations

import json

import pytest

from authoring_core.adapters import manifest
from authoring_core.adapters.units import UnitNotFound, root_of
from authoring_core.application.version_planning import (
    LevelBelowMinimum,
    apply_version,
    classify_diff,
    plan_version,
)
from authoring_core.domain.diff_rules import Level
from authoring_core.domain.release_tags import Release

from repos import PUBLISHED_SKILL, UNIT, git, make_repository, reset


class FakeReleases:
    """Los lanzamientos que le digamos, sin red."""

    def __init__(self, *tags: str, drafts: tuple[str, ...] = ()):
        self._releases = tuple(Release(tag=tag, is_draft=tag in drafts) for tag in tags)

    def list_releases(self, unit: str) -> tuple[Release, ...]:
        return self._releases


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    return make_repository(tmp_path_factory.mktemp("version"))


@pytest.fixture(autouse=True)
def _en_una_rama_de_trabajo(repo):
    reset(repo)
    git(repo, "switch", "-q", "-c", f"fix/{UNIT}")
    yield
    reset(repo)


def _unit_root(repo):
    return root_of(UNIT, repo)


def _commit(repo, message: str = "cambio") -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def _add_skill(repo, name: str = "nuevo") -> None:
    skill = _unit_root(repo) / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n\nCuerpo.\n", encoding="utf-8")


def _write_governance(repo, content: dict) -> None:
    (_unit_root(repo) / "GOVERNANCE.json").write_text(json.dumps(content, indent=2), encoding="utf-8")


def test_el_diff_se_acota_a_la_carpeta_de_la_unidad(repo):
    # Lo que se toque fuera no cambia la versión de la unidad.
    (repo / "README.md").write_text("otra cosa del repositorio\n", encoding="utf-8")
    _commit(repo)
    assert classify_diff(_unit_root(repo), repo).is_empty


def test_anadir_un_skill_sale_como_menor_desde_el_repositorio(repo):
    _add_skill(repo)
    _commit(repo)
    assert classify_diff(_unit_root(repo), repo).minimum is Level.MINOR


def test_retirar_un_skill_que_la_unidad_ya_ofrecia_sale_como_mayor(repo):
    (_unit_root(repo) / "skills" / PUBLISHED_SKILL / "SKILL.md").unlink()
    _commit(repo, "se retira el skill")
    assert classify_diff(_unit_root(repo), repo).minimum is Level.MAJOR


def test_anadir_y_borrar_en_la_misma_rama_no_cuenta_como_retirada(repo):
    # El diff es el neto contra la rama principal, y hace bien: para quien consume la unidad ese
    # artefacto nunca existió. La primera versión de la prueba de arriba se escribió así y por eso no
    # medía lo que decía medir.
    _add_skill(repo, "efimero")
    _commit(repo, "se añade")
    (_unit_root(repo) / "skills" / "efimero" / "SKILL.md").unlink()
    _commit(repo, "y se quita antes de publicar")
    assert classify_diff(_unit_root(repo), repo).is_empty


def test_mover_un_artefacto_cuenta_como_retirada_y_alta(repo):
    origen = _unit_root(repo) / "skills" / PUBLISHED_SKILL / "SKILL.md"
    destino = _unit_root(repo) / "skills" / "movido"
    destino.mkdir(parents=True)
    (destino / "SKILL.md").write_text(origen.read_text(encoding="utf-8"), encoding="utf-8")
    origen.unlink()
    _commit(repo, "movido de sitio")
    # Con la detección de renombrados activada saldría como un cambio de texto, que es justo la vía
    # para retirar un artefacto sin que se note.
    assert classify_diff(_unit_root(repo), repo).minimum is Level.MAJOR


def test_tocar_los_permisos_del_gobierno_sale_como_mayor_con_su_clave(repo):
    gobierno = json.loads((_unit_root(repo) / "GOVERNANCE.json").read_text(encoding="utf-8"))
    gobierno["permissions"] = {**gobierno.get("permissions", {}), "commands": ["python"]}
    _write_governance(repo, gobierno)
    _commit(repo)
    clasificacion = classify_diff(_unit_root(repo), repo)
    assert clasificacion.minimum is Level.MAJOR
    assert any(reason.key == "permissions" for reason in clasificacion.reasons)


def test_tocar_el_gobierno_sin_tocar_lo_que_puede_hacer_sale_como_parche(repo):
    gobierno = json.loads((_unit_root(repo) / "GOVERNANCE.json").read_text(encoding="utf-8"))
    gobierno["owner"] = {"team": "otro-equipo", "contact": "otro@example.com"}
    _write_governance(repo, gobierno)
    _commit(repo)
    assert classify_diff(_unit_root(repo), repo).minimum is Level.PATCH


def test_sin_ninguna_version_publicada_la_propuesta_es_la_de_una_unidad_nueva(repo):
    _add_skill(repo)
    _commit(repo)
    plan = plan_version(_unit_root(repo), UNIT, repo, releases=FakeReleases())
    assert plan.is_new_unit and str(plan.proposed) == "0.1.0-beta.1"


def test_la_ultima_publicada_sale_de_los_lanzamientos_y_no_del_manifiesto(repo):
    # El manifiesto de la rama principal puede ir por delante de lo que está publicado.
    _add_skill(repo)
    _commit(repo)
    plan = plan_version(
        _unit_root(repo), UNIT, repo, releases=FakeReleases(f"{UNIT}--v1.4.0", f"{UNIT}--v1.5.0")
    )
    assert str(plan.latest_published) == "1.5.0" and str(plan.proposed) == "1.6.0-beta.1"


def test_un_borrador_no_es_una_publicacion(repo):
    _add_skill(repo)
    _commit(repo)
    plan = plan_version(
        _unit_root(repo),
        UNIT,
        repo,
        releases=FakeReleases(f"{UNIT}--v1.4.0", f"{UNIT}--v9.0.0", drafts=(f"{UNIT}--v9.0.0",)),
    )
    assert str(plan.latest_published) == "1.4.0"


def test_los_lanzamientos_de_otra_unidad_del_repositorio_no_cuentan(repo):
    # Mezclarlos le daría a una unidad la versión de su vecina.
    _add_skill(repo)
    _commit(repo)
    plan = plan_version(_unit_root(repo), UNIT, repo, releases=FakeReleases("otra-unidad--v8.0.0"))
    assert plan.latest_published is None


def test_calcular_sin_aplicar_no_toca_ningun_archivo(repo):
    _add_skill(repo)
    _commit(repo)
    antes = (_unit_root(repo) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    plan_version(_unit_root(repo), UNIT, repo, releases=FakeReleases(f"{UNIT}--v1.0.0"))
    assert (_unit_root(repo) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8") == antes
    assert git(repo, "status", "--porcelain") == ""


def test_aplicar_escribe_la_version_en_el_manifiesto_y_en_ningun_otro_archivo(repo):
    _add_skill(repo)
    _commit(repo)
    plan, escrito = apply_version(
        _unit_root(repo), UNIT, Level.MINOR, repo, releases=FakeReleases(f"{UNIT}--v1.0.0")
    )
    assert manifest.read_version(_unit_root(repo)) == str(plan.proposed) == "1.1.0-beta.1"
    assert escrito.name == "plugin.json"
    tocados = [line.split(maxsplit=1)[1] for line in git(repo, "status", "--porcelain").splitlines()]
    assert tocados == [f"plugins/{UNIT}/.claude-plugin/plugin.json"]


def test_un_nivel_por_debajo_del_minimo_se_rechaza_y_no_escribe(repo):
    _add_skill(repo)
    _commit(repo)
    antes = manifest.read_version(_unit_root(repo))
    with pytest.raises(LevelBelowMinimum):
        apply_version(_unit_root(repo), UNIT, Level.PATCH, repo, releases=FakeReleases(f"{UNIT}--v1.0.0"))
    assert manifest.read_version(_unit_root(repo)) == antes


def test_el_autor_puede_subir_por_encima_del_minimo(repo):
    _add_skill(repo)
    _commit(repo)
    plan, _ = apply_version(
        _unit_root(repo), UNIT, Level.MAJOR, repo, releases=FakeReleases(f"{UNIT}--v1.0.0")
    )
    assert str(plan.proposed) == "2.0.0-beta.1"


def test_un_cambio_vacio_no_se_puede_aplicar(repo):
    with pytest.raises(LevelBelowMinimum):
        apply_version(_unit_root(repo), UNIT, Level.PATCH, repo, releases=FakeReleases())


def test_una_unidad_que_no_esta_en_el_repositorio_se_dice(repo):
    with pytest.raises(UnitNotFound):
        root_of("unidad-que-no-existe", repo)
