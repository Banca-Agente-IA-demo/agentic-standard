# Configuración MCP

Dos piezas, en dos archivos, sin repetir nada entre ellas:

| Pieza | Archivo | Quién lo lee |
|---|---|---|
| La **conexión**: comando o URL, transporte, cabeceras con `${VAR}` | `.mcp.json` en la raíz de la unidad | Los dos clientes. Copilot genera su configuración desde este mismo archivo (04 §2) |
| El **gobierno**: responsable, escritura y digest del contrato | bloque `mcp` de `metadata.governance`, en `plugin.json` | La automatización y Port |

**Una unidad, un servidor** (D2). `mcpServers` tiene exactamente una clave, el bloque `mcp` tiene esa
misma clave, y `permissions.mcp_servers` la lista como único elemento. Si un plugin necesita dos
servidores, son dos unidades. No hay excepción: la excepción es lo que rompe la cota de la aprobación.

**Puede publicarse sola**, sin skills ni agente: medido el 7 de septiembre de 2026 que un plugin con sólo
`plugin.json` y `.mcp.json` registra el servidor en los dos clientes. Cómo lo referenciaría un agente de
**otra** unidad está en medición (D7); mientras tanto, el agente que usa el servidor viaja en la misma
unidad.

Lo que el validador exige: ningún valor literal que parezca un secreto (C2); cada servidor con su
`accountable_team`, tenga credenciales o no; y el bloque `tools_contract` completo, con `digest`,
`write_operations` y `observed_at`. Qué credenciales hacen falta no se declara: son los `${VAR}` del
propio `.mcp.json`. Que el digest corresponda con lo que el servidor expone (C4) **hoy no se comprueba**:
el CI no tiene credenciales para conectarse, y el control está pendiente de rediseño.

`tools_contract` **no se teclea y esta plantilla no lo trae**: lo escribe entero el asistente tras
consultar `tools/list`. Un servidor que escribe fuera del cliente, o que pide credenciales, o cualquier
servidor externo, eleva el riesgo mínimo (03 §1).
Lo aprueban el Lead Técnico, Ciberseguridad y Riesgo operacional (02 §7.1).

Para un servidor local por `stdio`, la conexión es `{ "command": "npx", "args": ["-y", "<<PACKAGE>>"], "env": { "<<CREDENTIAL>>": "${<<CREDENTIAL>>}" } }` y el ejecutable va en `permissions.commands`.
