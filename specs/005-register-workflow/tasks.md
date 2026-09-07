# Tasks: El registro de un cambio en una rama de trabajo

**Input**: `specs/005-register-workflow/`

**Tests**: obligatorias para el descubrimiento (T1, T4). El workflow se prueba ejecutándolo.

## Phase 1: Descubrimiento de unidades (US2)

- [ ] T001 `tests/validator/test_discovery.py` y `validator/agentic_validator/domain/discovery.py`: la
      función pura que, dados los archivos cambiados y las raíces de unidad, devuelve las unidades
      tocadas. Casos: un archivo dentro de una unidad, uno fuera, la unidad más cercana cuando hay
      anidación, una unidad borrada entera, sin cambios.
- [ ] T002 `validator/agentic_validator/adapters/repository.py`: preguntar a git por los archivos
      cambiados desde una referencia, y recorrer el árbol buscando las raíces de unidad. Un fallo de
      git se convierte en motivo, no en excepción.
- [ ] T003 `tests/validator/test_repository.py`: con repositorios de git de verdad creados en
      `tmp_path`, incluidos el caso sin referencia común y el de la primera confirmación.

## Phase 2: Modo de descubrimiento del comando (US1, US2)

- [ ] T004 `cli.py`: el comando acepta una raíz de repositorio y una referencia de comparación, y
      entonces descubre y comprueba cada unidad tocada. Sin la referencia, sigue comprobando una sola
      unidad como hasta ahora.
- [ ] T005 El informe agrega varias unidades: cuántas se comprobaron, qué se encontró en cada una y un
      veredicto único. Sin unidades tocadas, dice que no había nada que comprobar y termina en verde.
- [ ] T006 Pruebas del modo de descubrimiento de punta a punta sobre un repositorio de mentira con dos
      unidades, una rota, tocando sólo la sana.

## Phase 3: La composite action (US3)

- [ ] T007 `.github/actions/validate/action.yml`: instala Python, instala el validador desde el árbol
      del propio estándar que la action trae consigo, y ejecuta el comando. Emite el informe al
      resumen de la ejecución. Distingue el fallo del validador del hallazgo de conformidad.
- [ ] T008 Comprobar en una ejecución real que la action resuelve el árbol del estándar sin ninguna
      credencial. Es el supuesto que hace que esto funcione en BCP con el repositorio privado.

## Phase 4: El reutilizable y el llamador (US1, US4)

- [ ] T009 `.github/workflows/register.yml` del estándar: sólo invocación, permisos vacíos arriba y
      mínimos por job, tiempo máximo, la firma documentada en la cabecera.
- [ ] T010 Etiquetar el estándar y mover la referencia movible con la que los dominios lo invocan.
- [ ] T011 `agents-modernization/.github/workflows/register.yml`: el llamador real, con el evento, la
      cancelación de la ejecución anterior de la rama, los permisos exactos y la referencia. Sin
      lógica y sin filtro de rutas.

## Phase 5: Evidencia de cierre del hito

- [ ] T012 Crear en una rama de trabajo del dominio una unidad hecha de las plantillas y empujarla;
      comprobar que la comprobación aparece con el nombre esperado y termina en verde (SC-001).
- [ ] T013 Estropear esa unidad, empujar, y comprobar que termina en rojo nombrando el archivo
      (SC-002).
- [ ] T014 Comprobar que la instalación del validador desde el repositorio funciona en PowerShell
      (SC-005).
- [ ] T015 Actualizar el README del validador con el modo de descubrimiento; PR con la spec enlazada;
      CI en verde; registrar el cierre del hito 1 en el traspaso.

---

## Dependencies & Execution Order

- Fase 1 antes que la 2. Dentro de cada tarea, la prueba antes que el código.
- Fase 3 después de la 2, porque la action invoca el modo nuevo.
- T010 después de fusionar las fases 1 a 4 en el estándar: la etiqueta apunta a un commit que ya
  contiene todo.
- Fase 5 al final, y ocurre en el repositorio de dominio, no en el del estándar.
