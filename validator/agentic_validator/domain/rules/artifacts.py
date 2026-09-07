"""Se hace cargo de lo que una unidad debe declarar por llevar artefactos de texto.

Un skill, un agente o un prompt sólo exponen al estándar su frontmatter, y su mera presencia obliga a
declarar cómo se trata el contenido externo (C3). La estructura interna de cada tipo la fija la
herramienta (04 §4) y aquí no se juzga.
"""

from __future__ import annotations

from agentic_validator.domain.findings import Finding, error
from agentic_validator.domain.snapshot import UnitSnapshot
from agentic_validator.domain.standard import GOVERNANCE_FILE, MAX_DESCRIPTION_LENGTH

# Los siete campos de gobierno que la demo guardaba en el frontmatter y que hoy viven en otro sitio.
GOVERNANCE_FIELDS_IN_FRONTMATTER = frozenset(
    {"id", "owner_team", "owner_contact", "status", "version", "standard_version", "data_classification"}
)

# C3 aplica a lo que interpreta contenido externo: skill, prompt y agente (03 §3). Una unidad que sólo
# expone un servidor o unos hooks no lo interpreta.
_TYPES_REQUIRING_EXTERNAL_CONTENT = ("skills", "prompts", "agents")


def check_artifact_names(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El nombre declarado y el que impone la ruta tienen que coincidir.

    Si no coinciden, el cliente no encuentra el artefacto: no da error, simplemente no aparece.
    """
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        if artifact.error:
            findings.append(
                error("artifact.frontmatter-unreadable", artifact.path, f"no se pudo interpretar: {artifact.error}")
            )
            continue
        front = artifact.frontmatter
        if front is None:
            findings.append(error("artifact.frontmatter-missing", artifact.path, "el archivo no lleva frontmatter"))
            continue
        declared = front.get("name")
        if not declared:
            findings.append(error("artifact.name-missing", artifact.path, "el frontmatter no declara nombre"))
        elif str(declared) != artifact.expected_name:
            findings.append(
                error(
                    "artifact.name-mismatch",
                    artifact.path,
                    f"declara el nombre {declared!r} y su ruta impone {artifact.expected_name!r}",
                )
            )
    return tuple(findings)


def check_artifact_descriptions(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """La descripción es lo que el modelo lee para decidir si usa el artefacto (04 §1)."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        front = artifact.frontmatter
        if front is None:
            continue
        description = str(front.get("description") or "").strip()
        if not description:
            findings.append(error("artifact.description-missing", artifact.path, "el frontmatter no declara descripción"))
        elif len(description) > MAX_DESCRIPTION_LENGTH:
            # Es lo único que se carga en CADA petición: pasarse degrada la selección de todo lo instalado.
            findings.append(
                error(
                    "artifact.description-too-long",
                    artifact.path,
                    f"la descripción tiene {len(description)} caracteres y el máximo del formato es {MAX_DESCRIPTION_LENGTH}",
                )
            )
    return tuple(findings)


def check_no_governance_in_frontmatter(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """El gobierno vive en su archivo; el frontmatter sólo lleva lo que el cliente lee (D1)."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        front = artifact.frontmatter or {}
        catalog = front.get("metadata")
        keys = set(front) | (set(catalog) if isinstance(catalog, dict) else set())
        leaked = sorted(GOVERNANCE_FIELDS_IN_FRONTMATTER & keys)
        if leaked:
            findings.append(
                error(
                    "artifact.governance-in-frontmatter",
                    artifact.path,
                    f"campos de gobierno en el frontmatter: {', '.join(leaked)}; viven en {GOVERNANCE_FILE}",
                )
            )
    return tuple(findings)


def check_catalog_metadata_is_text(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """D1: el mapa de catálogo es texto a texto, como define la especificación de skills."""
    findings: list[Finding] = []
    for artifact in snapshot.text_artifacts:
        catalog = (artifact.frontmatter or {}).get("metadata")
        if not isinstance(catalog, dict):
            continue
        non_text = sorted(key for key, value in catalog.items() if not isinstance(value, str))
        if non_text:
            findings.append(
                error(
                    "artifact.catalog-not-text",
                    artifact.path,
                    f"el mapa metadata debe ser texto a texto y no lo es en: {', '.join(non_text)}",
                )
            )
    return tuple(findings)


def check_external_content_declared(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C3 se exige según el tipo de lo que la unidad contiene, no siempre."""
    governance = snapshot.governance
    if governance is None:
        return ()
    interprets_external = any(getattr(snapshot, kind) for kind in _TYPES_REQUIRING_EXTERNAL_CONTENT)
    if not interprets_external:
        return ()
    if not str(governance.get("external_content") or "").strip():
        return (
            error(
                "artifact.external-content-missing",
                GOVERNANCE_FILE,
                "la unidad lleva artefactos que interpretan contenido externo y no declara cómo lo trata",
            ),
        )
    return ()
