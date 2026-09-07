# Contrato del comando `smoke-org`

Interfaz pública de la herramienta. Cambiarla es cambiar el contrato con quien la ejecuta.

## Invocación

```
smoke-org --env <nombre> [--environments-dir <ruta>] [--teams-file <ruta>] [--verbose]
```

| Argumento | Obligatorio | Por defecto | Qué hace |
|---|---|---|---|
| `--env` | sí | | Nombre del entorno: `demo`, `bcp` o cualquier `<nombre>.json` del directorio de entornos |
| `--environments-dir` | no | `tools/smoke_org/environments` del paquete instalado | Directorio de archivos de entorno |
| `--teams-file` | no | `config/teams.json` del repositorio | Mapa de papeles a equipos |
| `--verbose`, `-v` | no | apagado | Logging `DEBUG` en `stderr`: cada comando `gh` ejecutado y su duración |

## Salidas

- `stdout`: el informe legible. Nada más.
- `stderr`: logging (`INFO` por defecto).
- Código de salida: `0` pasa, `1` no pasa, `2` no se pudo comprobar. `2` prevalece sobre `1`.

Fallos de uso (entorno inexistente, JSON inválido, `gh` no instalado) terminan con código `2` y un
mensaje `ERROR` en `stderr`, porque tampoco se pudo comprobar.

## Formato del informe

Una línea por comprobación y ámbito, un bloque final con el veredicto. Ejemplo con un fallo:

```
Prueba de humo: entorno demo, organización Banca-Agente-IA-demo

[PASA]      org.settings        organización        plan=free permiso_base=read crear_repos=false
[PASA]      teams.exist         platform-team
...
[FALLA]     variables.present   agentic-marketplace esperado INDEX_CHANNEL=production, encontrado ausente
[PASA]      rulesets.contexts   agents-modernization
...

Resumen: 21 superadas, 1 fallida, 0 sin comprobar
Veredicto: NO PASA
```

Con comprobaciones sin consultar:

```
[SIN DATOS] secrets.present     agentic-standard    no se pudo consultar: gh: HTTP 403 Resource not accessible
...
Veredicto: NO SE PUDO COMPROBAR
```

Reglas del formato: la etiqueta de estado va entre corchetes y es una de tres; el `check_id` y el
ámbito son columnas fijas; cuando hay valor esperado y encontrado, se muestran los dos con las
palabras «esperado» y «encontrado». El texto está en español; los identificadores, en inglés.

## Archivo de entorno

`environments/<nombre>.json`:

```json
{
  "organization": "Banca-Agente-IA-demo",
  "plan": "free",
  "default_repository_permission": "read",
  "members_can_create_repositories": false,
  "platform_repositories": ["agentic-standard"],
  "marketplaces": [
    { "repository": "agentic-marketplace", "channel": "production" },
    { "repository": "agentic-marketplace-exp", "channel": "experimental" }
  ],
  "domain_repositories": ["agents-modernization"]
}
```

Claves en snake_case, en inglés, fijas. Una clave desconocida es un error de carga (código `2`).

## Compatibilidad

`gh` 2.40 o superior con sesión autenticada; ámbitos `read:org` y `repo` como mínimo. En la demo,
`admin:org` para leer instalaciones de Apps. Python 3.11 o superior.
