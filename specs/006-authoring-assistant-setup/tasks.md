# Tasks: El asistente de autoría existe como unidad publicable

**Input**: `specs/006-authoring-assistant-setup/`

**Tests**: obligatorias. Aquí protegen tres promesas que se rompen en silencio: que el núcleo no
arrastra dependencias, que las capas no se cruzan, y que el estándar se gobierna a sí mismo.

## Phase 1: La unidad publicable

- [x] T001 `.claude-plugin/plugin.json` y `GOVERNANCE.json` del asistente. El gobierno declara los
      ejecutables que usa y eleva el riesgo por encima del mínimo calculado.
- [x] T002 `validator.lock` con la etiqueta de versión concreta y su commit.
- [x] T003 `skills/author-unit/SKILL.md` con el frontmatter portable y el marco del diálogo.
- [x] T004 `README.md` del plugin: qué es, cómo está hecho, qué necesita la máquina del autor.

## Phase 2: El núcleo por capas

- [x] T005 `authoring_core/` con las cuatro capas, cada una declarando de qué se hace cargo.
- [x] T006 `tests/conftest.py`: importar el núcleo como lo harán los scripts, añadiendo la raíz del
      plugin al camino de búsqueda.
- [x] T007 `tests/test_package_shape.py`: el núcleo se importa sin instalar nada; sólo usa la
      biblioteca estándar; las capas existen y declaran su responsabilidad; la de reglas no habla con
      el exterior ni importa a las demás.

## Phase 3: El estándar se gobierna a sí mismo

- [x] T008 `tests/test_self_governance.py`: ninguna unidad propia tiene errores, y sus avisos son
      exactamente los declarados como esperados, en los dos sentidos.
- [x] T009 Ampliar las rutas del workflow de pruebas para cubrir `plugins/`, y añadir las pruebas del
      plugin a las que ejecuta el repositorio.

## Phase 4: Higiene de versiones del estándar

- [x] T010 Devolver la etiqueta de la versión concreta al commit que cerró el hito 1, y publicar una
      versión nueva para el estado posterior. Una etiqueta de versión concreta no se mueve; sólo la
      referencia mayor movible se mueve.

## Phase 5: La medición que puede cambiar la forma

- [ ] T011 Instalar el plugin en Copilot CLI desde este repositorio y comprobar que aparece listado.
- [ ] T012 Lo mismo en Claude Code.
- [ ] T013 Anotar lo medido en el traspaso y, si algo obliga a mover la forma, hacerlo ahora que el
      esqueleto está vacío.

---

## Dependencies & Execution Order

- Las fases 1 a 4 están hechas y son independientes de la 5.
- La fase 5 es interactiva y ocurre en la máquina del usuario. Es el punto de decisión del hito: lo
  que se mida ahí confirma o cambia la forma antes de escribir el núcleo determinístico.
