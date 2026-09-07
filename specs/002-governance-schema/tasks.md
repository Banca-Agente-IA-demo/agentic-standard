# Tasks: Esquemas de gobierno y de marketplace

**Input**: `specs/002-governance-schema/`

**Tests**: obligatorias (constitución IV, T1 a T6). Aquí el entregable es el contrato y sus pruebas.

## Phase 1: Copia del material de diseño

- [ ] T001 Copiar `hito-1-esquemas-y-plantillas/schemas/governance.schema.json` y
      `marketplace.schema.json` a `schemas/`, sin modificar un byte; comprobarlo con `diff`.
- [ ] T002 Copiar las cuatro instancias de ejemplo a `tests/schemas/fixtures/` con nombres que digan
      qué son; añadir `README.md` con la procedencia de cada una y la advertencia de que los esquemas
      se editan primero en el paquete de diseño.

## Phase 2: Dependencias y CI

- [ ] T003 Añadir `jsonschema` a las dependencias de desarrollo de `pyproject.toml`.
- [ ] T004 Ampliar las rutas de `.github/workflows/tests.yml` para incluir `schemas/**`.

## Phase 3: Pruebas del contrato de gobierno (US1 y US2)

- [ ] T005 `tests/schemas/conftest.py`: carga de los dos esquemas, construcción de los validadores
      (gobierno y las dos proyecciones del índice) y el helper que devuelve la lista de errores.
- [ ] T006 `tests/schemas/test_governance_schema.py`, historia 1: los dos ejemplos válidos pasan;
      bucle sobre los nueve campos retirados de la demo; bucle sobre los cinco obligatorios; `id` con
      la forma antigua de puntos.
- [ ] T007 Mismo archivo, historia 2: dos servidores en `mcp`; dos en `permissions.mcp_servers`;
      credenciales sin custodio y sin credenciales sin custodio; `tools_digest` sin prefijo; bloque
      `approval` de la demo; comodín en `tools`; `deprecation` incompleta; fecha no ISO;
      `superseded_by` igual a `none`; `risk_level` fuera del enumerado; `x_extensions` libre.

## Phase 4: Pruebas del contrato del índice (US3)

- [ ] T008 `tests/schemas/test_marketplace_schema.py`: cada índice contra su proyección y contra la
      ajena; índice vacío; metadatos de compilación en la versión; sufijo en la versión del índice;
      la raíz rechaza todo.

## Phase 5: Cierre

- [ ] T009 `pytest -q` en verde en local; comprobar que ninguna prueba del hito 0 se rompe.
- [ ] T010 Actualizar el `README.md` de la raíz con la fila de `schemas/` ya llena; PR con la spec
      enlazada y el Constitution Check; CI en verde en 3.11 y 3.12.

---

## Dependencies & Execution Order

- T001 y T002 antes que todo lo demás.
- T003 y T004 en paralelo, antes de ejecutar pruebas.
- T005 antes que T006, T007 y T008. T006 y T007 tocan el mismo archivo, así que van en orden; T008 es
  independiente y puede ir en paralelo con ellas.
- T009 y T010 al final.
