"""Identidad y versión: un desajuste aquí se propaga a la etiqueta, al índice y al catálogo."""

from __future__ import annotations

from agentic_validator.domain.rules import identity

from tests.validator.units import REPOSITORY, UNIT_NAME, snapshot, with_governance


def _rules(snap) -> list[str]:
    findings = (
        identity.check_files_present(snap)
        + identity.check_id_matches_tree(snap)
        + identity.check_manifest_version(snap)
        + identity.check_manifest_fields(snap)
    )
    return [f.rule for f in findings]


def test_una_unidad_bien_formada_no_produce_hallazgos_de_identidad():
    assert _rules(snapshot()) == []


def test_sin_gobierno_o_sin_identidad_hay_un_hallazgo_por_cada_archivo_ausente():
    for field, rule in (("governance", "identity.governance-missing"), ("manifest", "identity.manifest-missing")):
        assert rule in _rules(snapshot(**{field: None})), field


def test_un_archivo_de_gobierno_ilegible_se_informa_como_hallazgo_y_no_como_excepcion():
    snap = snapshot(governance=None, governance_error="JSON inválido: línea 3")
    assert "identity.governance-unreadable" in _rules(snap)


def test_el_identificador_que_no_empieza_por_el_repositorio_es_error():
    snap = snapshot(governance=with_governance(id=f"otro-repo/{UNIT_NAME}"))
    assert "identity.id-repository" in _rules(snap)


def test_el_identificador_que_no_termina_en_el_nombre_del_directorio_es_error():
    snap = snapshot(governance=with_governance(id=f"{REPOSITORY}/otro-nombre"))
    assert "identity.id-directory" in _rules(snap)


def test_el_identificador_que_no_coincide_con_el_nombre_de_la_identidad_es_error():
    snap = snapshot(manifest={"name": "otro", "version": "0.1.0"})
    assert "identity.id-manifest-name" in _rules(snap)


def test_una_version_que_no_es_semver_estricta_es_error():
    # La etiqueta debe coincidir con esta versión y el índice la copia (02 §7.1).
    for bad in ("1.0", "v1.0.0", "1.0.0+build.7", "01.0.0", ""):
        snap = snapshot(manifest={"name": UNIT_NAME, "version": bad})
        assert "identity.version-not-semver" in _rules(snap), bad


def test_una_version_con_sufijo_de_prelanzamiento_es_valida():
    # Toda versión nace con sufijo: es lo que decide el canal.
    snap = snapshot(manifest={"name": UNIT_NAME, "version": "0.1.0-beta.1"})
    assert "identity.version-not-semver" not in _rules(snap)


def test_una_identidad_sin_version_es_error():
    snap = snapshot(manifest={"name": UNIT_NAME})
    assert "identity.version-missing" in _rules(snap)


def test_un_campo_fuera_del_formato_de_identidad_es_error():
    snap = snapshot(manifest={"name": UNIT_NAME, "version": "0.1.0", "dependencies": ["otra-unidad"]})
    assert "identity.manifest-unknown-fields" in _rules(snap)


def test_una_identidad_sin_schema_es_error():
    # El $schema del manifiesto sí es público y resuelve desde el editor, al contrario que el del
    # gobierno, que por eso lleva schema_version (D5).
    snap = snapshot(manifest={"name": UNIT_NAME, "version": "0.1.0"})
    assert "identity.manifest-schema-missing" in _rules(snap)
