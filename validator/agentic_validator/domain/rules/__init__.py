"""La lista de reglas de la unidad y el recorrido que las ejecuta todas.

Cada regla es una función pura de la instantánea a sus hallazgos. El recorrido no se detiene en la
primera que falla: el autor tiene que ver todo lo que le falta de una vez.
"""

from __future__ import annotations

from collections.abc import Callable

from agentic_validator.domain.model import Finding, UnitSnapshot
from agentic_validator.domain.rules import artifacts, hooks, hygiene, identity, layout, mcp, permissions, risk

Rule = Callable[[UnitSnapshot], tuple[Finding, ...]]

ALL_RULES: tuple[Rule, ...] = (
    identity.check_files_present,
    identity.check_id_matches_tree,
    identity.check_manifest_version,
    identity.check_manifest_fields,
    permissions.check_declared_permissions_are_lists,
    permissions.check_agent_tools,
    permissions.check_hook_commands,
    mcp.check_mcp_readable,
    mcp.check_single_server,
    mcp.check_governance_block_matches,
    mcp.check_credentials_match,
    mcp.check_no_literal_secrets,
    hooks.check_hooks_readable,
    hooks.check_hook_events_are_portable,
    hooks.check_hook_timeouts,
    hooks.check_hook_commands_stay_inside,
    hooks.check_hooks_do_not_download,
    artifacts.check_artifact_names,
    artifacts.check_artifact_descriptions,
    artifacts.check_no_governance_in_frontmatter,
    artifacts.check_catalog_metadata_is_text,
    artifacts.check_agent_mcp_spellings,
    artifacts.check_external_content_declared,
    artifacts.check_eval_suites,
    artifacts.check_every_artifact_has_its_suite,
    layout.check_no_nested_unit,
    layout.check_artifacts_are_in_their_directory,
    layout.check_hooks_bring_tests,
    hygiene.check_no_absolute_paths,
    hygiene.check_no_secrets_in_files,
    hygiene.check_no_orphan_support_files,
    risk.check_declared_risk_is_not_lower,
)


def run_rules(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for rule in ALL_RULES:
        findings.extend(rule(snapshot))
    return tuple(findings)
