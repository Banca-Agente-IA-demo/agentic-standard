# Quickstart: Prueba de humo de la organización

Cómo ejecutar y validar la capacidad de punta a punta. Los detalles del contrato están en
[contracts/cli.md](contracts/cli.md) y el modelo en [data-model.md](data-model.md).

## Requisitos

- Python 3.11 o superior.
- `gh` autenticado: `gh auth status` debe mostrar la cuenta con `read:org` y `repo` (en la demo,
  también `admin:org`).
- Clon de `agentic-standard`.

## Instalación (una vez por clon)

```
python -m pip install -e ".[dev]"
```

## Ejecutar contra la demo

```
smoke-org --env demo
echo $LASTEXITCODE      # PowerShell; en bash: echo $?
```

Esperado al cerrar el hito 0: todas las líneas `[PASA]`, `Veredicto: PASA`, código `0`.

## Validar que detecta un fallo (escenario 2 de la historia 1)

1. Retirar una variable: `gh variable delete AGENTIC_TOPIC --repo Banca-Agente-IA-demo/agentic-marketplace`
2. `smoke-org --env demo`: la línea `variables.present` de `agentic-marketplace` sale `[FALLA]` con
   «esperado AGENTIC_TOPIC=agentic-unit, encontrado ausente»; veredicto `NO PASA`; código `1`.
3. Restaurar: `gh variable set AGENTIC_TOPIC --repo Banca-Agente-IA-demo/agentic-marketplace --body agentic-unit`
4. `smoke-org --env demo` vuelve a `0`.

## Validar «no se pudo comprobar» (escenario 4)

Con una sesión sin `admin:org` (o tras `gh auth logout` en una terminal aparte), `smoke-org --env demo`
marca `app.installed` como `[SIN DATOS]` con el mensaje de `gh`, veredicto `NO SE PUDO COMPROBAR`,
código `2`.

## Pruebas automáticas

```
pytest -q
```

Cubren: cada comprobación del dominio con datos (superada, fallida, sin datos), la regla del
veredicto, el parseo de las fixtures reales de `gh` con un runner falso, y el caso de uso con un
lector falso. Sin red ni disco fuera de `tmp_path`.

## CI

`.github/workflows/tests.yml` corre `pytest` en Python 3.11 y 3.12 en cada PR a `main` que toque
`tools/`, `tests/`, `config/teams.json` o `pyproject.toml`.
