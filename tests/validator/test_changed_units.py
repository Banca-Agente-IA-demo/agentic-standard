"""El modo de descubrimiento: sólo se juzga lo que el push ha tocado, sobre repositorios de verdad."""

from __future__ import annotations

import json
import subprocess

import pytest

from agentic_validator.cli import main, review_changed_units
from agentic_validator.domain.model import Verdict

from tests.validator.units import add_skill, build_unit, read_governance, write_governance

pytestmark = pytest.mark.slow


def _git(repository, *args) -> None:
    subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True, text=True)


def _domain_repository(tmp_path):
    """Un repositorio de dominio con dos unidades confirmadas: una sana y otra rota a propósito.

    La rota lo está por lo mismo que le pasaría a quien copia una unidad para partir de ella y no
    cambia su identificador: el `id` sigue terminando en el nombre de la unidad original.
    """
    sana = build_unit(tmp_path)
    root = sana.parents[1]
    assert root.name == "agents-demo", root

    rota = root / "plugins" / "dos"
    (rota / ".claude-plugin").mkdir(parents=True)
    for archivo in ("GOVERNANCE.json", ".claude-plugin/plugin.json"):
        (rota / archivo).write_text((sana / archivo).read_text(encoding="utf-8"), encoding="utf-8")

    _git(tmp_path, "init", "-q", "-b", "main", str(root))
    _git(root, "config", "user.email", "prueba@example.com")
    _git(root, "config", "user.name", "prueba")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "dos unidades")
    return root


def test_solo_se_comprueba_la_unidad_tocada_aunque_otra_este_rota(tmp_path):
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/algo")
    add_skill(root / "plugins" / "demo-unit")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "toca la sana")
    run = review_changed_units(root, "main")
    assert [informe.unit for informe in run.reports] == ["demo-unit"]
    assert run.verdict is Verdict.COMPLIANT


def test_tocar_la_unidad_rota_la_señala(tmp_path):
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/otra")
    (root / "plugins" / "dos" / "README.md").write_text("algo\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "toca la rota")
    run = review_changed_units(root, "main")
    assert [informe.unit for informe in run.reports] == ["dos"]
    assert run.verdict is Verdict.NOT_COMPLIANT


def test_un_cambio_fuera_de_toda_unidad_no_comprueba_nada_y_termina_en_verde(tmp_path):
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/docs")
    (root / "README.md").write_text("documentación\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "sólo documentación")
    run = review_changed_units(root, "main")
    assert run.reports == () and run.verdict is Verdict.COMPLIANT


def test_sin_referencia_con_la_que_comparar_se_comprueban_todas(tmp_path):
    # Comprobar de más es molesto; callar es peligroso.
    root = _domain_repository(tmp_path)
    run = review_changed_units(root, "origin/no-existe")
    assert sorted(informe.unit for informe in run.reports) == ["demo-unit", "dos"]


def test_el_comando_en_modo_descubrimiento_devuelve_cero_y_lo_dice(tmp_path, capsys):
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/docs")
    (root / "README.md").write_text("documentación\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "sólo documentación")
    assert main([str(root), "--changed-since", "main"]) == Verdict.COMPLIANT.exit_code
    salida = capsys.readouterr().out
    assert "no había nada que comprobar" in salida and "Veredicto: CUMPLE" in salida


def test_el_formato_estructurado_del_modo_descubrimiento_lista_cada_unidad(tmp_path, capsys):
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/algo")
    add_skill(root / "plugins" / "demo-unit")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "toca la sana")
    main([str(root), "--changed-since", "main", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["units_checked"] == 1 and payload["units"][0]["unit"] == "demo-unit"


def test_una_unidad_borrada_entera_no_se_comprueba(tmp_path):
    # Sus archivos salen en el diff, pero ya no hay nada que juzgar.
    root = _domain_repository(tmp_path)
    _git(root, "switch", "-q", "-c", "feat/borra")
    _git(root, "rm", "-r", "-q", "plugins/dos")
    _git(root, "commit", "-q", "-m", "borra la rota")
    run = review_changed_units(root, "main")
    assert [informe.unit for informe in run.reports] == []
