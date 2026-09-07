"""Hooks: el único tipo que ejecuta código propio sin que nadie lo invoque.

Reglas medidas (D3) o exigidas por C5: tope de tiempo en cada acción, comando dentro de la unidad,
ninguna descarga en ejecución, y eventos que disparen en los dos clientes.
"""

from __future__ import annotations

from agentic_validator.domain.model import (
    HOOKS_FILE,
    PLUGIN_ROOT_PREFIX,
    PORTABLE_HOOK_EVENTS,
    Finding,
    UnitSnapshot,
    error,
    warning,
)

# El campo que la demo anterior aceptaba «durante la migración» y que no existe en el formato. Aquí es
# error desde el primer día: la organización nace limpia.
INVENTED_TIMEOUT_FIELD = "timeoutSec"

# Un comando que trae algo de la red en tiempo de ejecución se salta el sello por completo (C5).
_DOWNLOADERS = ("curl", "wget", "iwr", "invoke-webrequest")


def command_actions(snapshot: UnitSnapshot) -> tuple[tuple[str, dict], ...]:
    """Cada acción de tipo comando con el evento al que cuelga. Compartido con las reglas de permisos."""
    hooks = (snapshot.hooks or {}).get("hooks")
    if not isinstance(hooks, dict):
        return ()
    found: list[tuple[str, dict]] = []
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            actions = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(actions, list):
                continue
            found.extend((str(event), action) for action in actions if isinstance(action, dict))
    return tuple(found)


def check_hooks_readable(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    if snapshot.hooks_error:
        return (error("hooks.unreadable", HOOKS_FILE, f"no se pudo interpretar: {snapshot.hooks_error}"),)
    return ()


def check_hook_events_are_portable(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Un evento fuera de la lista no falla en el cliente: no dispara nunca (D3).

    Avisa en vez de bloquear hasta que el lineamiento 04 §2 fije la lista.
    """
    events = {event for event, _ in command_actions(snapshot)}
    outside = sorted(events - PORTABLE_HOOK_EVENTS)
    return tuple(
        warning(
            "hooks.event-not-portable",
            HOOKS_FILE,
            f"el evento {event!r} no está medido en los dos clientes; puede no dispararse nunca",
        )
        for event in outside
    )


def check_hook_timeouts(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Un hook sin tope puede colgar el cliente de quien lo instale."""
    findings: list[Finding] = []
    for event, action in command_actions(snapshot):
        if INVENTED_TIMEOUT_FIELD in action:
            findings.append(
                error(
                    "hooks.invented-timeout-field",
                    HOOKS_FILE,
                    f"el hook de {event} usa {INVENTED_TIMEOUT_FIELD!r}, que no existe en el formato; el campo es 'timeout'",
                )
            )
        if "timeout" not in action:
            findings.append(
                error("hooks.timeout-missing", HOOKS_FILE, f"el hook de {event} no declara tope de tiempo")
            )
    return tuple(findings)


def check_hook_commands_stay_inside(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """C5: una ruta fuera de la unidad no existe en la máquina de nadie más y ejecuta algo sin sellar."""
    findings: list[Finding] = []
    for event, action in command_actions(snapshot):
        command = str(action.get("command", ""))
        if command.startswith(PLUGIN_ROOT_PREFIX):
            continue
        if _looks_like_system_executable(command):
            continue
        findings.append(
            error(
                "hooks.command-outside-unit",
                HOOKS_FILE,
                f"el comando del hook de {event} no apunta dentro de la unidad con {PLUGIN_ROOT_PREFIX}",
            )
        )
    return tuple(findings)


def _looks_like_system_executable(command: str) -> bool:
    """Un ejecutable del sistema declarado en permissions.commands, sin ruta: `mvn -q verify`."""
    first = command.strip().split()[0] if command.strip() else ""
    return bool(first) and "/" not in first and "\\" not in first and not first.startswith("$")


def check_hooks_do_not_download(snapshot: UnitSnapshot) -> tuple[Finding, ...]:
    """Un `curl … | bash` se salta el sello por completo."""
    findings: list[Finding] = []
    for event, action in command_actions(snapshot):
        command = str(action.get("command", "")).lower()
        if any(downloader in command for downloader in _DOWNLOADERS):
            findings.append(
                error(
                    "hooks.command-downloads",
                    HOOKS_FILE,
                    f"el comando del hook de {event} descarga en ejecución; eso ejecuta algo que no se selló",
                )
            )
    return tuple(findings)
