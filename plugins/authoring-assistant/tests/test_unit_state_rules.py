"""El estado de la unidad, con datos: qué se deriva de los lanzamientos y qué no se afirma."""

from __future__ import annotations

from authoring_core.domain.release_tags import Release
from authoring_core.domain.unit_state import (
    STATE_DEVELOPMENT,
    STATE_EXPERIMENTAL,
    STATE_INDETERMINATE,
    STATE_PRODUCTION,
    classify,
)

UNIT = "demo-unidad"


def _released(*tags: str) -> tuple[Release, ...]:
    return tuple(Release(tag=tag, is_draft=False) for tag in tags)


def _drafts(*tags: str) -> tuple[Release, ...]:
    return tuple(Release(tag=tag, is_draft=True) for tag in tags)


def test_sin_ningun_lanzamiento_la_unidad_esta_en_desarrollo():
    estado = classify((), UNIT)
    assert estado.state == STATE_DEVELOPMENT and not estado.can_be_deprecated


def test_en_desarrollo_el_mensaje_dice_que_no_hay_nada_que_deprecar():
    assert "nada que deprecar" in classify((), UNIT).message


def test_solo_con_prelanzamientos_la_unidad_es_experimental():
    estado = classify(_released(f"{UNIT}--v0.1.0-beta.1", f"{UNIT}--v0.2.0-beta.3"), UNIT)
    assert estado.state == STATE_EXPERIMENTAL and not estado.has_final


def test_con_una_version_final_la_unidad_esta_en_produccion():
    estado = classify(_released(f"{UNIT}--v1.0.0-beta.1", f"{UNIT}--v1.0.0"), UNIT)
    assert estado.state == STATE_PRODUCTION and estado.has_final


def test_una_beta_por_delante_no_saca_a_la_unidad_de_produccion():
    # Una versión nueva nace experimental y convive con la de producción: la transición es de la
    # unidad, no de la versión publicada.
    estado = classify(_released(f"{UNIT}--v1.0.0", f"{UNIT}--v1.1.0-beta.1"), UNIT)
    assert estado.state == STATE_PRODUCTION and estado.prerelease_in_flight


def test_sin_beta_por_delante_no_se_anuncia_ninguna():
    assert not classify(_released(f"{UNIT}--v1.0.0"), UNIT).prerelease_in_flight


def test_la_ultima_publicada_es_la_mayor_en_orden_semver():
    estado = classify(_released(f"{UNIT}--v1.9.0", f"{UNIT}--v1.10.0"), UNIT)
    assert str(estado.latest) == "1.10.0"


def test_solo_se_deprecan_las_unidades_publicadas():
    for releases, esperado in (
        ((), False),
        (_released(f"{UNIT}--v0.1.0-beta.1"), True),
        (_released(f"{UNIT}--v1.0.0"), True),
    ):
        assert classify(releases, UNIT).can_be_deprecated is esperado, releases


def test_una_unidad_con_lanzamientos_en_borrador_no_se_da_por_en_desarrollo():
    # Suspender y retirar ponen los lanzamientos en borrador, así que una unidad suspendida tiene
    # cero publicados. Responderle «en desarrollo: nada que deprecar» sería decirle algo falso.
    estado = classify(_drafts(f"{UNIT}--v1.0.0"), UNIT)
    assert estado.state == STATE_INDETERMINATE and not estado.can_be_deprecated


def test_lo_indeterminado_dice_que_puede_estar_suspendida_o_retirada():
    assert "suspendida o retirada" in classify(_drafts(f"{UNIT}--v1.0.0"), UNIT).message


def test_un_borrador_no_cuenta_como_publicado_cuando_hay_publicados():
    estado = classify(_released(f"{UNIT}--v1.0.0") + _drafts(f"{UNIT}--v9.0.0"), UNIT)
    assert str(estado.latest) == "1.0.0"


def test_los_lanzamientos_de_otra_unidad_no_dicen_nada_de_esta():
    # Mezclarlos daría por publicada una unidad que no lo está.
    assert classify(_released("otra-unidad--v3.0.0"), UNIT).state == STATE_DEVELOPMENT


def test_una_etiqueta_que_no_es_una_version_se_descarta_sin_romper_nada():
    estado = classify(_released("nightly", f"{UNIT}--v1.0.0"), UNIT)
    assert estado.state == STATE_PRODUCTION and str(estado.latest) == "1.0.0"
