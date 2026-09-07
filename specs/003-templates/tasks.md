# Tasks: Plantillas de unidad y de artefacto

**Input**: `specs/003-templates/`

**Tests**: obligatorias (constitución IV, T1 a T6).

## Phase 1: Copia del material de diseño

- [ ] T001 Copiar `hito-1-esquemas-y-plantillas/templates/` a `templates/` sin modificar un byte;
      comprobarlo con `diff -r`.

## Phase 2: Dependencias y CI

- [ ] T002 Añadir `pyyaml` a las dependencias de desarrollo de `pyproject.toml`.
- [ ] T003 Ampliar las rutas de `.github/workflows/tests.yml` para incluir `templates/**`.

## Phase 3: Instanciación y plantillas de unidad (US1)

- [ ] T004 `tests/templates/markers.py`: el mapa de valores de prueba de cada marcador, la expresión
      regular que los reconoce, y la función que instancia un texto y falla si queda alguno.
- [ ] T005 `tests/templates/test_unit_templates.py`: las dos plantillas de gobierno instanciadas
      validan contra el esquema; la agrupada con el bloque del servidor pegado también; ningún
      marcador queda sin valor de prueba en ninguna plantilla; las dos plantillas de identidad son
      JSON válido, con versión SemVer estricta y sin campos fuera de los permitidos.

## Phase 4: Plantillas de artefacto (US2 y US3)

- [ ] T006 `tests/templates/test_artifact_templates.py`, historia 2: bucle sobre skill, agente y
      prompt; ninguna clave de gobierno en el mapa de catálogo; todos los valores del mapa son texto;
      nombre y descripción presentes.
- [ ] T007 Mismo archivo, historia 3: la suite tiene al menos tres casos, todos con categoría, las
      tres categorías presentes y una aserción mecánica por caso; la plantilla de hooks declara tope
      de tiempo con el nombre correcto, nunca el campo inventado de la demo, apunta dentro de la
      unidad y usa sólo eventos de la lista portable.

## Phase 5: Cierre

- [ ] T008 `pytest -q` en verde; ninguna prueba anterior se rompe.
- [ ] T009 `README.md` de la raíz con la fila de `templates/` ya llena; PR con la spec enlazada y el
      Constitution Check; CI en verde en 3.11 y 3.12.

---

## Dependencies & Execution Order

- T001 antes que todo.
- T002 y T003 en paralelo.
- T004 antes que T005; T006 y T007 tocan el mismo archivo y van en orden, pero son independientes de
  T005 y pueden ir en paralelo con ella.
- T008 y T009 al final.
- La rama parte de `feat/002-governance-schema`, no de `main`, porque las pruebas validan contra
  `schemas/`. Se rebasa sobre `main` cuando la spec 002 se fusione.
