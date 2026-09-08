"""La tabla de las reglas de versión, fila por fila, con datos y sin repositorio."""

from __future__ import annotations

from authoring_core.domain.diff_rules import Change, FileChange, Level, classify_changes


def _minimum(*changes: FileChange) -> Level | None:
    return classify_changes(changes).minimum


def _modified(path: str, *keys: str) -> FileChange:
    return FileChange(path=path, change=Change.MODIFIED, touched_keys=keys)


def test_tocar_lo_que_la_unidad_puede_hacer_es_mayor():
    for key in ("permissions", "risk_level", "data_classification"):
        assert _minimum(_modified("GOVERNANCE.json", key)) is Level.MAJOR, key


def test_tocar_la_conexion_o_los_hooks_es_mayor():
    for path in (".mcp.json", "hooks/hooks.json", "hooks/scripts/check.sh"):
        assert _minimum(_modified(path)) is Level.MAJOR, path


def test_anadir_un_artefacto_es_menor():
    for path in ("skills/nuevo/SKILL.md", "agents/revisor.agent.md", "commands/publicar.md"):
        assert _minimum(FileChange(path, Change.ADDED)) is Level.MINOR, path


def test_cambiar_el_texto_de_un_artefacto_que_ya_estaba_es_parche():
    assert _minimum(_modified("skills/demo/SKILL.md")) is Level.PATCH


def test_cambiar_solo_la_suite_de_evaluacion_es_parche():
    assert _minimum(_modified("evals/demo/promptfooconfig.yaml")) is Level.PATCH


def test_quitar_un_artefacto_de_una_unidad_publicada_es_mayor():
    # El documento no tiene fila para la eliminación, así que caía en la última y salía parche. Quien
    # invoca un skill retirado se entera en ejecución.
    for path in ("skills/demo/SKILL.md", "agents/revisor.agent.md", "commands/publicar.md"):
        assert _minimum(FileChange(path, Change.DELETED)) is Level.MAJOR, path


def test_quitar_un_archivo_que_no_es_artefacto_no_eleva_por_si_solo():
    # Elevar por cualquier borrado convertiría en mayor la limpieza de un archivo muerto.
    assert _minimum(FileChange("evals/demo/casos.yaml", Change.DELETED)) is Level.PATCH


def test_cuando_el_cambio_cae_en_varias_filas_manda_la_mas_alta():
    resultado = classify_changes(
        (
            _modified("skills/demo/SKILL.md"),
            FileChange("skills/otro/SKILL.md", Change.ADDED),
            _modified("GOVERNANCE.json", "permissions"),
        )
    )
    assert resultado.minimum is Level.MAJOR


def test_los_motivos_de_todas_las_filas_constan_aunque_mande_una():
    # Si sólo constara el que manda, el autor no vería el resto del cambio en el menú.
    resultado = classify_changes(
        (_modified("skills/demo/SKILL.md"), _modified("GOVERNANCE.json", "permissions"))
    )
    assert {reason.level for reason in resultado.reasons} == {Level.MAJOR, Level.PATCH}


def test_cada_motivo_nombra_la_ruta_y_la_clave_que_lo_justifica():
    motivo = classify_changes((_modified("GOVERNANCE.json", "permissions"),)).reasons[0]
    assert motivo.path == "GOVERNANCE.json" and motivo.key == "permissions"


def test_un_cambio_vacio_no_propone_ningun_salto():
    vacio = classify_changes(())
    assert vacio.is_empty and vacio.minimum is None


def test_cambiar_el_gobierno_sin_tocar_lo_que_la_unidad_puede_hacer_es_parche():
    assert _minimum(_modified("GOVERNANCE.json", "owner")) is Level.PATCH


def test_el_manifiesto_no_cuenta_porque_es_donde_vive_la_version():
    # Contarlo sería circular: cambia en todo salto, así que todo salto seria al menos parche por sí
    # mismo aunque no hubiera nada más.
    assert classify_changes((_modified(".claude-plugin/plugin.json"),)).is_empty
