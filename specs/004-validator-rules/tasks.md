# Tasks: El validador del estándar y su comando de reglas

**Input**: `specs/004-validator-rules/`

**Tests**: obligatorias (constitución IV, T1 a T6). Las reglas se prueban con instantáneas en memoria.

## Phase 1: Paquete y empaquetado (US6)

- [x] T001 `validator/pyproject.toml` con distribución propia, comando `rules`, dependencias de
      ejecución declaradas (incluida la que la demo usaba sin declarar) y la inyección del contrato de
      gobierno desde `../schemas` al construir. **Verificado**: el esquema entra en el paquete y es
      idéntico al del repositorio.
- [ ] T002 Añadir `dist/` y `*.whl` al `.gitignore`; ampliar las rutas del workflow de pruebas para
      cubrir `validator/**`.
- [ ] T003 `tests/validator/test_packaging.py`: construir el paquete y comprobar que el contrato de
      gobierno que lleva dentro es byte a byte el de `schemas/`.

## Phase 2: Tipos y lectura (base de todo)

- [ ] T004 `validator/agentic_validator/model.py`: severidad, hallazgo con sus constructores, informe
      con veredicto y códigos de salida, nivel de riesgo, y los tipos de la instantánea de la unidad.
      Sin I/O.
- [ ] T005 `validator/agentic_validator/frontmatter.py`: lector corto de frontmatter. Ausencia
      devuelve ausencia; YAML inválido devuelve el motivo.
- [ ] T006 `validator/agentic_validator/reading.py`: de la carpeta de la unidad a la instantánea.
      JSON o YAML corruptos se convierten en motivo, no en excepción.
- [ ] T007 `tests/validator/snapshots.py`: constructores de instantáneas para las pruebas de reglas,
      con una unidad válida por defecto y sustituciones puntuales.

## Phase 3: Reglas de identidad y permisos (US2 y US3)

- [ ] T008 `tests/validator/test_rules_identity.py` y `rules/identity.py`: el gobierno valida contra
      el contrato; la primera mitad del identificador es el repositorio; la segunda es el nombre del
      manifiesto; el directorio coincide; versión estrictamente conforme; campos del manifiesto dentro
      de los permitidos.
- [ ] T009 `tests/validator/test_rules_permissions.py` y `rules/permissions.py`: herramientas de cada
      agente contra las declaradas; ejecutables de cada hook contra los declarados; servidor de la
      configuración contra el declarado.

## Phase 4: Reglas del servidor y de los hooks (US2 y US5)

- [ ] T010 `tests/validator/test_rules_mcp.py` y `rules/mcp.py`: como mucho un servidor; la misma
      clave en configuración, gobierno y permisos; bloque de gobierno si y sólo si hay configuración;
      credenciales cotejadas en los dos sentidos; valor literal que parece credencial.
- [ ] T011 `tests/validator/test_rules_hooks.py` y `rules/hooks.py`: tope de tiempo presente y con el
      nombre correcto; ruta dentro de la unidad; sin descarga en ejecución; eventos portables como
      aviso.

## Phase 5: Reglas de artefactos y de riesgo (US1, US4 y US5)

- [ ] T012 `tests/validator/test_rules_artifacts.py` y `rules/artifacts.py`: nombre declarado igual al
      del archivo o directorio; descripción no vacía; declaración de tratamiento de contenido externo
      según el tipo; las dos grafías del agente que restringe servidor y el aviso si no restringe;
      forma de la suite cuando la unidad la trae.
- [ ] T013 `tests/validator/test_rules_risk.py` y `rules/risk.py`: mínimo calculado por cada hecho;
      declarar por debajo falla; declarar por encima pasa.

## Phase 6: Recorrido, informe y comando (US1)

- [ ] T014 `rules/__init__.py`: la lista de reglas y el recorrido que las ejecuta todas sin detenerse.
- [ ] T015 `validator/agentic_validator/report.py`: informe legible y estructurado.
- [ ] T016 `validator/agentic_validator/cli.py`: argumentos, logging, cableado y código de salida.

## Phase 7: Validación de punta a punta y cierre

- [ ] T017 `tests/validator/test_reading.py`: instanciar las plantillas de la spec 003 en `tmp_path`
      como unidad real y comprobar que el validador no encuentra hallazgos (SC-002); estropear cada
      comprobación y ver su hallazgo.
- [ ] T018 Instalar el paquete en un entorno limpio y ejecutar el comando sobre esa unidad (SC-004).
- [ ] T019 `validator/README.md`; fila de `validator/` en el `README.md` de la raíz; revisión contra
      el checklist de `AGENTS.md`; PR con la spec enlazada y el CI en verde en 3.11 y 3.12.

---

## Dependencies & Execution Order

- Fase 1 primero; T001 ya está hecha y verificada.
- Fase 2 antes que cualquier regla. T004 antes que T005 a T007.
- Fases 3, 4 y 5 son independientes entre sí una vez existe la instantánea; dentro de cada una, la
  prueba antes que la regla.
- Fase 6 después de las reglas. Fase 7 al final.
