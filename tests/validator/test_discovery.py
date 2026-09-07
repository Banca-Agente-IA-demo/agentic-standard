"""Sólo se juzga lo que el autor ha tocado: la regla pura, con datos (T1)."""

from __future__ import annotations

from agentic_validator.domain.discovery import owning_unit, units_touched

ROOTS = ("plugins/uno", "skills/dos")


def test_un_archivo_dentro_de_una_unidad_la_señala():
    assert units_touched(("plugins/uno/SKILL.md",), ROOTS) == ("plugins/uno",)


def test_un_archivo_fuera_de_toda_unidad_no_señala_ninguna():
    # Tocar el README del repositorio no es tocar una unidad.
    assert units_touched(("README.md", ".github/workflows/register.yml"), ROOTS) == ()


def test_varios_archivos_de_la_misma_unidad_la_señalan_una_sola_vez():
    changed = ("plugins/uno/GOVERNANCE.json", "plugins/uno/skills/a/SKILL.md")
    assert units_touched(changed, ROOTS) == ("plugins/uno",)


def test_archivos_de_unidades_distintas_las_señalan_todas_y_ordenadas():
    changed = ("skills/dos/SKILL.md", "plugins/uno/GOVERNANCE.json")
    assert units_touched(changed, ROOTS) == ("plugins/uno", "skills/dos")


def test_una_unidad_borrada_entera_no_se_señala():
    # Sus archivos aparecen en el diff, pero ya no está entre las raíces: no hay nada que juzgar.
    assert units_touched(("plugins/tres/GOVERNANCE.json",), ROOTS) == ()


def test_sin_archivos_cambiados_no_hay_unidades():
    assert units_touched((), ROOTS) == ()


def test_sin_unidades_en_el_repositorio_no_hay_nada_que_señalar():
    assert units_touched(("plugins/uno/SKILL.md",), ()) == ()


def test_con_unidades_anidadas_gana_la_mas_cercana_al_archivo():
    # Anidar no debería ocurrir y la regla de layout lo señala; si ocurre, el archivo es de la interior.
    anidadas = ("plugins/uno", "plugins/uno/dentro")
    assert owning_unit("plugins/uno/dentro/SKILL.md", anidadas) == "plugins/uno/dentro"
    assert owning_unit("plugins/uno/SKILL.md", anidadas) == "plugins/uno"


def test_un_prefijo_de_nombre_no_cuenta_como_pertenencia():
    # `plugins/uno-bis` no está dentro de `plugins/uno` aunque su ruta empiece igual.
    assert owning_unit("plugins/uno-bis/SKILL.md", ROOTS) is None


def test_la_propia_raiz_de_la_unidad_cuenta_como_suya():
    assert owning_unit("plugins/uno", ROOTS) == "plugins/uno"
