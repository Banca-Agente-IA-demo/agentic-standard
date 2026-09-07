"""Identidad y versión: que el repositorio, el nombre y la versión digan lo mismo en todo el árbol.

Un desajuste aquí se propaga a la etiqueta, al índice y a la ficha del catálogo, y sólo se descubre
al instalar.
"""

from __future__ import annotations

import re

from agentic_validator.domain.model import (
    ALLOWED_MANIFEST_FIELDS,
    GOVERNANCE_FILE,
    MANIFEST_FILE,
    Finding,
    UnitSnapshot,
    error,
)

# SemVer 2.0.0 con sufijo de prelanzamiento opcional y sin metadatos de compilación. La etiqueta debe
# coincidir con esta versión y el índice la copia (02 §7.1).
STRICT_SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(-(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*)?$"
)


def check_files_present(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Toda unidad publicable lleva identidad y gobierno, sea plugin o artefacto individual."""
    findings: list[Finding] = []
    if snapshot.governance is None and snapshot.governance_error is None:
        findings.append(error("identity.governance-missing", GOVERNANCE_FILE, "la unidad no declara su gobierno"))
    if snapshot.governance_error:
        findings.append(
            error("identity.governance-unreadable", GOVERNANCE_FILE, f"no se pudo interpretar: {snapshot.governance_error}")
        )
    if snapshot.manifest is None and snapshot.manifest_error is None:
        findings.append(error("identity.manifest-missing", MANIFEST_FILE, "la unidad no declara su identidad"))
    if snapshot.manifest_error:
        findings.append(
            error("identity.manifest-unreadable", MANIFEST_FILE, f"no se pudo interpretar: {snapshot.manifest_error}")
        )
    return tuple(findings)


def check_id_matches_tree(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El identificador tiene forma repo/name y sus dos mitades son hechos del árbol."""
    governance = snapshot.governance
    if governance is None:
        return ()
    declared = governance.get("id")
    if not isinstance(declared, str) or "/" not in declared:
        return ()  # la forma la impone el contrato; aquí sólo se comparan las mitades
    repository, name = declared.split("/", 1)
    findings: list[Finding] = []
    if repository != snapshot.repository:
        findings.append(
            error(
                "identity.id-repository",
                GOVERNANCE_FILE,
                f"el identificador empieza por {repository!r} y la unidad vive en {snapshot.repository!r}",
            )
        )
    if name != snapshot.name:
        findings.append(
            error(
                "identity.id-directory",
                GOVERNANCE_FILE,
                f"el identificador termina en {name!r} y el directorio de la unidad se llama {snapshot.name!r}",
            )
        )
    manifest_name = (snapshot.manifest or {}).get("name")
    if manifest_name is not None and manifest_name != name:
        findings.append(
            error(
                "identity.id-manifest-name",
                MANIFEST_FILE,
                f"la identidad declara el nombre {manifest_name!r} y el gobierno termina en {name!r}",
            )
        )
    return tuple(findings)


def check_manifest_version(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """La versión es obligatoria y estrictamente conforme: la etiqueta y el índice la copian."""
    manifest = snapshot.manifest
    if manifest is None:
        return ()
    version = manifest.get("version")
    if version is None:
        return (error("identity.version-missing", MANIFEST_FILE, "la identidad no declara versión"),)
    if not isinstance(version, str) or not STRICT_SEMVER.match(version):
        return (
            error(
                "identity.version-not-semver",
                MANIFEST_FILE,
                f"la versión {version!r} no es SemVer estricta sin metadatos de compilación",
            ),
        )
    return ()


def check_manifest_fields(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El formato de identidad permite un conjunto cerrado de campos de primer nivel."""
    manifest = snapshot.manifest
    if manifest is None:
        return ()
    unknown = sorted(set(manifest) - ALLOWED_MANIFEST_FIELDS)
    if unknown:
        return (
            error(
                "identity.manifest-unknown-fields",
                MANIFEST_FILE,
                f"campos fuera del formato de identidad: {', '.join(unknown)}",
            ),
        )
    findings: list[Finding] = []
    if not manifest.get("name"):
        findings.append(error("identity.manifest-name-missing", MANIFEST_FILE, "la identidad no declara nombre"))
    if not manifest.get("$schema"):
        # Es público y sí resuelve desde el editor, al contrario que el del gobierno (D5).
        findings.append(
            error("identity.manifest-schema-missing", MANIFEST_FILE, "la identidad no declara $schema")
        )
    return tuple(findings)
