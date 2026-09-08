"""La versión propuesta, con datos: precedencia, contador de prelanzamiento y orden estricto."""

from __future__ import annotations

import pytest

from authoring_core.domain.diff_rules import Level
from authoring_core.domain.versions import (
    FIRST_VERSION_OF_A_NEW_UNIT,
    VersionError,
    highest,
    is_at_least,
    next_version,
    parse,
    parse_or_none,
)


def _next(current: str | None, published: str | None, level: Level) -> str:
    return str(
        next_version(
            parse(current) if current else None,
            parse(published) if published else None,
            level,
        )
    )


def test_una_unidad_sin_version_publicada_nace_en_la_version_inicial():
    assert _next(None, None, Level.MINOR) == FIRST_VERSION_OF_A_NEW_UNIT


def test_cada_nivel_sube_su_numero_y_pone_a_cero_los_de_la_derecha():
    for level, esperado in (
        (Level.MAJOR, "2.0.0-beta.1"),
        (Level.MINOR, "1.6.0-beta.1"),
        (Level.PATCH, "1.5.4-beta.1"),
    ):
        assert _next("1.5.3", "1.5.3", level) == esperado, level


def test_toda_version_propuesta_nace_con_sufijo_de_prelanzamiento():
    for level in Level:
        assert "-beta." in _next("1.5.3", "1.5.3", level), level


def test_un_prelanzamiento_en_vuelo_absorbe_los_cambios_de_su_nivel_o_inferiores():
    # La principal va por delante de lo publicado con una beta que aún no ha salido.
    for level in (Level.MINOR, Level.PATCH):
        assert _next("1.6.0-beta.1", "1.5.3", level) == "1.6.0-beta.2", level


def test_un_cambio_de_nivel_superior_sube_el_numero_y_reinicia_el_contador():
    assert _next("1.6.0-beta.2", "1.5.3", Level.MAJOR) == "2.0.0-beta.1"


def test_la_propuesta_es_siempre_estrictamente_mayor_que_la_ultima_publicada():
    # Con la regla antigua, ir de 0.1.0 a 0.0.1 pasaba el gate.
    for current, published, level in (
        ("0.1.0", "0.1.0", Level.PATCH),
        ("1.5.3", "2.0.0", Level.PATCH),
        ("1.5.3", "1.6.0", Level.MINOR),
    ):
        propuesta = parse(_next(current, published, level))
        assert propuesta > parse(published), (current, published, level)


def test_un_prelanzamiento_va_antes_que_la_final_del_mismo_numero():
    assert parse("1.5.0-beta.2") > parse("1.5.0-beta.1")
    assert parse("1.5.0-beta.2") < parse("1.5.0")


def test_una_cadena_que_no_es_una_version_se_rechaza():
    for texto in ("v1.0.0", "1.0", "1.0.0-rc.1", "1.0.0+build.5", "uno.dos.tres"):
        with pytest.raises(VersionError):
            parse(texto)
        assert parse_or_none(texto) is None, texto


def test_entre_varias_versiones_gana_la_mayor_en_orden_semver():
    # Ordenar como texto pondría 1.10.0 antes que 1.9.0.
    versiones = tuple(parse(t) for t in ("1.9.0", "1.10.0", "1.10.0-beta.3", "0.1.0"))
    assert str(highest(versiones)) == "1.10.0"


def test_sin_ninguna_version_no_hay_mayor():
    assert highest(()) is None


def test_el_autor_puede_subir_por_encima_del_minimo_pero_nunca_por_debajo():
    assert is_at_least(Level.MAJOR, Level.MINOR)
    assert is_at_least(Level.MINOR, Level.MINOR)
    assert not is_at_least(Level.PATCH, Level.MINOR)


def test_si_la_principal_va_por_detras_de_lo_publicado_se_avanza_sobre_lo_publicado():
    # Pasa cuando alguien publicó desde otra rama. Contar desde la principal daría una versión que ya
    # existe con otro contenido.
    assert _next("1.0.0", "9.9.9", Level.PATCH) == "9.9.10-beta.1"
