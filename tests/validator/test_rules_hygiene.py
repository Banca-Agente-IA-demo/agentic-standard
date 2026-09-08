"""Higiene del contenido versionado (C2): rutas absolutas, secretos en claro y apoyo huérfano."""

from __future__ import annotations

from agentic_validator.domain.rules import hygiene

from tests.validator.units import snapshot


def _rules(snap) -> list[str]:
    findings = (
        hygiene.check_no_absolute_paths(snap)
        + hygiene.check_no_secrets_in_files(snap)
        + hygiene.check_no_orphan_support_files(snap)
    )
    return [f.rule for f in findings]


# --- Rutas absolutas -------------------------------------------------------------------------------


def test_una_ruta_absoluta_en_un_archivo_ejecutable_es_error():
    # Sólo existe en la máquina de quien la escribió.
    for ruta in ("/home/ana/scripts/x.sh", "C:\\Users\\ana\\x.ps1", "/usr/local/bin/tool"):
        contents = {"hooks/scripts/check.sh": f"#!/bin/sh\n{ruta} --run\n"}
        assert "hygiene.absolute-path" in _rules(snapshot(text_contents=contents)), ruta


def test_una_ruta_de_la_unidad_no_es_una_ruta_absoluta():
    contents = {"hooks/scripts/check.sh": "#!/bin/sh\n${CLAUDE_PLUGIN_ROOT}/hooks/scripts/otro.sh\n"}
    assert _rules(snapshot(text_contents=contents)) == []


def test_una_ruta_en_la_prosa_de_un_documento_no_se_juzga():
    # En un README una ruta suele ser un ejemplo; el ruido ahí no aporta.
    contents = {"README.md": "Instálalo en /usr/local/share si quieres.\n"}
    assert _rules(snapshot(text_contents=contents)) == []


# --- Secretos en claro -----------------------------------------------------------------------------


def test_un_token_de_proveedor_es_error_en_cualquier_archivo():
    # El prefijo no admite otra lectura, así que también se busca en la documentación: un token
    # pegado en un README sale del banco igual que uno pegado en la conexión.
    for valor in (
        "ghp_" + "a1b2c3d4e5" * 4,
        "sk-" + "Ab3xZ9qL7wR2tY5uP0mN",
        "xoxb-1234567890-abcdefghij",
        "AKIAIOSFODNN7EXAMPLB",
        "-----BEGIN RSA PRIVATE KEY-----",
        "Bearer Ab3xZ9qL7wR2tY5uP0mN4k",
    ):
        contents = {"README.md": f"Ejemplo de configuración: {valor}\n"}
        assert "hygiene.literal-secret" in _rules(snapshot(text_contents=contents)), valor


def test_una_credencial_asignada_en_un_archivo_de_configuracion_es_error():
    # Medido al escribir la regla: con la clave entrecomillada, como en cualquier JSON, la comilla de
    # cierre se colaba entre la clave y los dos puntos y la asignación no se reconocía.
    contents = {"config/settings.json": '{"api_key": "aB3xZ9qL7wR2tY5u"}\n'}
    assert "hygiene.literal-secret" in _rules(snapshot(text_contents=contents))


def test_una_referencia_a_una_variable_no_es_un_secreto():
    # La unidad viaja con el nombre de la variable; el valor lo pone quien la instala.
    for valor in ("${JIRA_TOKEN}", "${env:JIRA_TOKEN}", "$(cat /run/secrets/token)"):
        contents = {"config/settings.json": f'{{"api_key": "{valor}"}}\n'}
        assert _rules(snapshot(text_contents=contents)) == [], valor


def test_un_hueco_de_plantilla_no_es_un_secreto():
    # Las plantillas de la spec 003 llevan justamente estos valores; avisar de ellas haría que el
    # autor desactivara la regla el primer día.
    for valor in ("<TU_API_KEY>", "REPLACE_WITH_YOUR_TOKEN", "changeme-changeme", "example-value-here"):
        contents = {"config/settings.json": f'{{"api_key": "{valor}"}}\n'}
        assert _rules(snapshot(text_contents=contents)) == [], valor


def test_un_valor_de_entropia_baja_no_es_un_secreto():
    # Un digesto de ejemplo con ceros es largo y no es una credencial: lo que lo delata es que
    # repite el mismo puñado de caracteres.
    for valor in ("0" * 32, "aaaaaaaaaaaaaaaa", "sha256:" + "0" * 64):
        contents = {"config/settings.json": f'{{"secret": "{valor}"}}\n'}
        assert _rules(snapshot(text_contents=contents)) == [], valor


def test_una_asignacion_en_la_prosa_de_un_documento_no_se_juzga():
    # Documentar `password: <lo-que-sea>` es lo normal en un README; la forma del valor sólo se
    # juzga en archivos de configuración o de código.
    contents = {"docs/guia.md": "Escribe `password: aB3xZ9qL7wR2tY5u` en tu entorno local.\n"}
    assert _rules(snapshot(text_contents=contents)) == []


# --- Recursos huérfanos ----------------------------------------------------------------------------


def test_un_archivo_de_apoyo_que_nadie_referencia_es_aviso():
    # No rompe nada: viaja en cada instalación y no se usa, así que avisa y no bloquea.
    snap = snapshot(
        files=("skills/demo/SKILL.md", "skills/demo/references/guia.md"),
        text_contents={"skills/demo/SKILL.md": "---\nname: demo\n---\n\n# Título\n"},
    )
    findings = hygiene.check_no_orphan_support_files(snap)
    assert [f.rule for f in findings] == ["hygiene.orphan-support-file"]
    assert not findings[0].blocks


def test_un_archivo_de_apoyo_referenciado_no_produce_aviso():
    snap = snapshot(
        files=("skills/demo/SKILL.md", "skills/demo/references/guia.md"),
        text_contents={"skills/demo/SKILL.md": "Lee [la guía](references/guia.md) antes de empezar.\n"},
    )
    assert _rules(snap) == []


def test_un_archivo_fuera_de_una_carpeta_de_apoyo_no_se_juzga_como_huerfano():
    # El artefacto y su gobierno los lee el cliente, no el artefacto: pedir que alguien los
    # mencione sería un aviso imposible de atender.
    snap = snapshot(files=("skills/demo/SKILL.md", "GOVERNANCE.json", ".claude-plugin/plugin.json"))
    assert _rules(snap) == []


def test_un_modulo_que_otro_script_importa_no_es_huerfano():
    # Medido sobre el asistente de autoría: `_entry.py` lo importan los tres puntos de entrada, pero
    # el texto del import no contiene la extensión, así que la regla lo avisaba como peso muerto.
    snap = snapshot(
        files=("skills/demo/SKILL.md", "skills/demo/scripts/_entry.py", "skills/demo/scripts/estado.py"),
        text_contents={
            "skills/demo/SKILL.md": "Ejecuta `scripts/estado.py`.\n",
            "skills/demo/scripts/estado.py": "from _entry import emit\n",
        },
    )
    assert _rules(snap) == []
