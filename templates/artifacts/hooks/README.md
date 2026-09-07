# Hooks

`hooks/hooks.json` en la raíz de la unidad, con sus scripts en `hooks/scripts/` y sus pruebas en
`hooks/tests/`. Es el único tipo que **ejecuta código propio sin que nadie lo invoque**, y por eso lo
aprueba Ciberseguridad además del Lead Técnico (02 §7.1). Copilot lee este archivo en formato Claude Code
tal cual, con `timeout` en la acción y `${CLAUDE_PLUGIN_ROOT}` expandido (medido el 7 de septiembre de
2026).

## Eventos portables

Sólo entran al núcleo portable los eventos que **disparan en los dos clientes con la misma grafía**,
medidos con un mismo `hooks.json` (D3, MEDICION-HOOKS-MCP-PORTABILIDAD.md §1):

| Evento | Claude Code 2.1.263 | Copilot CLI 1.0.83 |
|---|---|---|
| `SessionStart` | dispara | dispara (después de `UserPromptSubmit`) |
| `UserPromptSubmit` | dispara | dispara |
| `PreToolUse` | dispara | dispara |
| `PostToolUse` | dispara | dispara |
| `Stop` | dispara | dispara |
| `SessionEnd` | dispara | dispara |

Un evento mal escrito **no falla: simplemente no dispara nunca**, y el autor cree que su control está
activo. Por eso la lista es cerrada. Un evento fuera de la lista **avisa** en el hito 1 y **fallará**
cuando 04 §2 la fije. Lo exclusivo de un cliente se documenta en `x_extensions` del `GOVERNANCE.json`.
`SubagentStop`, `PreCompact`, `Notification` y `PermissionRequest` no están medidos: fuera hasta que lo estén.

No asumas el orden entre eventos: Copilot dispara `UserPromptSubmit` antes que `SessionStart`.

## Lo que el validador exige

- **`timeout` en segundos, en cada acción**, y por debajo del techo del estándar. Un hook sin tope puede
  colgar el cliente de quien lo instale. `timeoutSec` **no existe** en el formato y es error, no aviso.
- **El comando apunta dentro de la unidad**, con `${CLAUDE_PLUGIN_ROOT}/…` (C5). Una ruta absoluta no
  existe en la máquina de nadie más y ejecuta algo que no se selló.
- **El comando no descarga nada en ejecución.** Un `curl … | bash` se salta el sello por completo.
- **El ejecutable está en `permissions.commands`** del `GOVERNANCE.json` (C1).
- **Trae pruebas** en `hooks/tests/` que ejercitan el script con entrada y salida observables; las corre
  `verify.yml` (C5).

La presencia de este archivo eleva el riesgo mínimo calculado de la unidad (03 §1).
