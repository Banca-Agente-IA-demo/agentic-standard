# Configuración MCP

Dos piezas, en dos archivos, sin repetir nada entre ellas:

| Pieza | Archivo | Quién lo lee |
|---|---|---|
| La **conexión**: comando o URL, transporte, cabeceras con `${VAR}` | `.mcp.json` en la raíz de la unidad | Los dos clientes. Copilot genera su configuración desde este mismo archivo (04 §2) |
| El **gobierno**: escritura, credenciales, custodio, digest del contrato | bloque `mcp` del `GOVERNANCE.json` | La automatización y Port |

**Una unidad, un servidor** (D2). `mcpServers` tiene exactamente una clave, el bloque `mcp` tiene esa
misma clave, y `permissions.mcp_servers` la lista como único elemento. Si un plugin necesita dos
servidores, son dos unidades. No hay excepción: la excepción es lo que rompe la cota de la aprobación.

**Puede publicarse sola**, sin skills ni agente: medido el 7 de septiembre de 2026 que un plugin con sólo
`plugin.json` y `.mcp.json` registra el servidor en los dos clientes. Cómo lo referenciaría un agente de
**otra** unidad está en medición (D7); mientras tanto, el agente que usa el servidor viaja en la misma
unidad.

Lo que el validador exige: los `${VAR}` de `.mcp.json` coinciden uno a uno con `credentials`; ningún
valor literal que parezca un secreto (C2); `tools_digest` corresponde con lo que el servidor expone (C4).
Un servidor con `write_operations: true` o con credenciales eleva el riesgo mínimo a `medium` (03 §1).
Lo aprueban el Lead Técnico, Ciberseguridad y Riesgo operacional (02 §7.1).

Para un servidor local por `stdio`, la conexión es `{ "command": "npx", "args": ["-y", "<<PACKAGE>>"], "env": { "<<CREDENTIAL>>": "${<<CREDENTIAL>>}" } }` y el ejecutable va en `permissions.commands`.
