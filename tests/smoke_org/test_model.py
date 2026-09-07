"""Veredicto y validación del entorno: reglas puras, sin disco ni red (T1)."""

from smoke_org.model import (
    CheckResult,
    CheckStatus,
    Environment,
    IndexChannel,
    Marketplace,
    Report,
    Verdict,
    validate_environment,
    verdict_of,
)


def _report(*statuses: CheckStatus) -> Report:
    results = tuple(CheckResult("x", "y", status) for status in statuses)
    return Report("demo", "org", results)


def test_sin_fallos_ni_sin_datos_el_veredicto_es_pasa():
    assert verdict_of(_report(CheckStatus.PASSED, CheckStatus.PASSED)) is Verdict.PASS


def test_un_solo_fallo_basta_para_no_pasar():
    assert verdict_of(_report(CheckStatus.PASSED, CheckStatus.FAILED)) is Verdict.FAIL


def test_sin_datos_prevalece_sobre_fallo():
    # Clarify 3 de la spec: un informe incompleto no puede decir «no pasa» con certeza.
    assert verdict_of(_report(CheckStatus.FAILED, CheckStatus.UNCHECKED)) is Verdict.UNCHECKED


def test_cada_veredicto_tiene_su_codigo_de_salida_del_contrato():
    for verdict, code in ((Verdict.PASS, 0), (Verdict.FAIL, 1), (Verdict.UNCHECKED, 2)):
        assert verdict.exit_code == code, verdict


def _environment(**overrides) -> Environment:
    base = dict(
        name="demo",
        organization="Org",
        plan="free",
        default_repository_permission="read",
        members_can_create_repositories=False,
        platform_repositories=("standard",),
        marketplaces=(Marketplace("mkt", IndexChannel.PRODUCTION), Marketplace("mkt-exp", IndexChannel.EXPERIMENTAL)),
        domain_repositories=("agents-a",),
    )
    return Environment(**{**base, **overrides})


def test_un_entorno_completo_es_valido():
    assert validate_environment(_environment()) == ()


def test_organizacion_vacia_es_error():
    assert validate_environment(_environment(organization="  "))


def test_sin_marketplaces_es_error():
    assert validate_environment(_environment(marketplaces=()))


def test_dos_marketplaces_con_el_mismo_canal_es_error():
    same = (Marketplace("a", IndexChannel.PRODUCTION), Marketplace("b", IndexChannel.PRODUCTION))
    assert validate_environment(_environment(marketplaces=same))


def test_un_repositorio_en_dos_listas_es_error():
    assert validate_environment(_environment(platform_repositories=("agents-a",)))
