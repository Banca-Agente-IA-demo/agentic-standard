"""Higiene del contenido versionado (C2): que la unidad no lleve dentro nada que no deba salir.

Tres cosas que sólo se ven mirando los archivos, no el gobierno: una ruta que sólo existe en la
máquina de quien la escribió, una credencial escrita en claro y un archivo de apoyo que nadie usa.

El límite honesto de estas reglas es que escanean el paquete propio, no lo que un servidor devuelve
en ejecución. Son puras: reciben el texto ya leído y devuelven hallazgos.
"""

from __future__ import annotations

import re

from agentic_validator.domain.findings import Finding, error, warning
from agentic_validator.domain.snapshot import UnitSnapshot
from agentic_validator.domain.standard import (
    CONFIGURATION_SUFFIXES,
    MIN_SECRET_DISTINCT_CHARS,
    MIN_SECRET_VALUE_LENGTH,
    SECRET_ASSIGNMENT_KEYS,
    SUPPORT_DIRECTORIES,
)

# Una ruta absoluta versionada apunta a la máquina de quien la escribió.
_ABSOLUTE_PATH = re.compile(r"(?:^|[\s\"'(=])(?:/(?:usr|home|opt|etc|var|tmp|Users)/|[A-Za-z]:[\\/])")

# Prefijos de proveedor: una cadena que empieza así no puede ser otra cosa que una credencial, así
# que se buscan en TODOS los archivos de texto, documentación incluida.
_PROVIDER_TOKENS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "token de GitHub"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"), "clave de API de un proveedor de modelo"),
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}"), "token de Slack"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "clave de acceso de AWS"),
    (re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"), "clave privada"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{20,}"), "cabecera Authorization con token literal"),
)

# Una clave sospechosa con un valor pegado. Sólo se mira en archivos de configuración: en la prosa de
# un documento `password: ...` es casi siempre el ejemplo de lo que NO hay que hacer. La comilla
# opcional tras la clave es obligatoria para que funcione en JSON, donde la clave va entrecomillada.
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(" + "|".join(SECRET_ASSIGNMENT_KEYS) + r")\b[\"']?\s*[:=]\s*[\"']?([^\s\"',]+)"
)

# Marcas de que el valor es una referencia o un hueco por rellenar, no el secreto. `${VAR}` lo expande
# el cliente; `<...>`, `%...%` y `$(...)` son plantilla.
_REFERENCE_MARKS = ("${", "$(", "<", ">", "%", "{{")
_PLACEHOLDER_WORDS = ("example", "placeholder", "changeme", "change_me", "replace", "your", "tu_", "dummy", "sample")


def check_no_absolute_paths(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C2: una ruta absoluta versionada sólo existe en la máquina de quien la escribió."""
    findings: list[Finding] = []
    for path, text in sorted(snapshot.text_contents.items()):
        if not path.endswith(CONFIGURATION_SUFFIXES):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if _ABSOLUTE_PATH.search(line):
                findings.append(
                    error(
                        "hygiene.absolute-path",
                        f"{path}:{number}",
                        "hay una ruta absoluta; use ${CLAUDE_PLUGIN_ROOT} o una ruta relativa a la unidad",
                    )
                )
                break
    return tuple(findings)


def check_no_secrets_in_files(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C2: la unidad viaja sin el secreto, y eso vale para todos sus archivos, no sólo la conexión."""
    findings: list[Finding] = []
    for path, text in sorted(snapshot.text_contents.items()):
        for number, line in enumerate(text.splitlines(), start=1):
            what = _secret_in(line, scan_assignments=path.endswith(CONFIGURATION_SUFFIXES))
            if what is None:
                continue
            findings.append(
                error(
                    "hygiene.literal-secret",
                    f"{path}:{number}",
                    f"hay un valor con pinta de {what}; la unidad viaja con el nombre de la variable, no con el valor",
                )
            )
            break
    return tuple(findings)


def check_no_orphan_support_files(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Un archivo de apoyo que nadie referencia viaja en cada instalación y no se usa nunca.

    Es aviso y no error a propósito: no rompe nada, sólo engorda la unidad, y el material puede ser
    del autor deliberadamente no referenciado. Bloquear por esto rechazaría algo legítimo.
    """
    return tuple(
        warning(
            "hygiene.orphan-support-file",
            path,
            "ningún artefacto de la unidad lo referencia: viaja en el paquete y no se usa",
        )
        for path in sorted(snapshot.files)
        if _is_support_file(path) and not _is_mentioned(path, snapshot.text_contents)
    )


def _secret_in(line: str, *, scan_assignments: bool) -> str | None:
    """Qué credencial parece llevar la línea, o `None` si no parece llevar ninguna."""
    for pattern, what in _PROVIDER_TOKENS:
        if pattern.search(line):
            return what
    if not scan_assignments:
        return None
    for key, value in _SECRET_ASSIGNMENT.findall(line):
        if _looks_like_a_literal_secret(value):
            return f"{key} en claro"
    return None


def _looks_like_a_literal_secret(value: str) -> bool:
    if any(mark in value for mark in _REFERENCE_MARKS):
        return False
    if len(value) < MIN_SECRET_VALUE_LENGTH:
        return False
    if any(word in value.lower() for word in _PLACEHOLDER_WORDS):
        return False
    # Entropía baja: un digesto de ejemplo con ceros o una cadena repetida no es un secreto.
    return len(set(value)) >= MIN_SECRET_DISTINCT_CHARS


def _is_support_file(path: str) -> bool:
    parts = path.split("/")
    return any(part in SUPPORT_DIRECTORIES for part in parts[:-1])


def _is_mentioned(path: str, text_contents: dict[str, str]) -> bool:
    """El detector es permisivo a propósito: un falso positivo aquí hace que NO se avise, que es el
    lado seguro cuando lo que está en juego es sólo peso muerto."""
    name = path.rsplit("/", 1)[-1]
    for other, text in text_contents.items():
        if other == path:
            continue  # un archivo no se referencia a sí mismo
        if name in text or path in text:
            return True
    return False
