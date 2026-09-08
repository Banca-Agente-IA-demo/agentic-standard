# Feature Specification: El registro de un cambio en una rama de trabajo

**Feature Branch**: `feat/005-register-workflow`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `std-004-register-workflow` del PLAN-GLOBAL §5, hito 1. Es la última spec del hito.

**Depende de**: las specs 002, 003 y 004, ya en `main`.

**Input**: `FLUJO-CICLO-DE-VIDA.md` (flujo 1), `DISENO-FLUJOS-CICLO-DE-VIDA.md` §1.1 (qué workflow
sirve cada flujo) y `BUENAS-PRACTICAS-WORKFLOWS.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El autor ve si su unidad cumple sin salir de su rama (Priority: P1)

Quien está construyendo una unidad empuja su rama de trabajo y, sin hacer nada más, la automatización
le dice si lo que lleva escrito cumple las reglas del estándar. No tiene que abrir una solicitud de
cambio ni pedir revisión para enterarse.

**Why this priority**: es el flujo 1 entero y el criterio de cierre del hito. Y es lo que hace que la
solicitud de cambio llegue ya limpia: quien la abre sabe de antemano lo que le van a decir.

**Independent Test**: empujar una rama con una unidad bien formada y ver la comprobación en verde;
estropear un archivo, empujar, y verla en rojo señalando ese archivo.

**Acceptance Scenarios**:

1. **Given** una rama de trabajo con una unidad que cumple, **When** se empuja, **Then** la
   comprobación del registro termina en verde.
2. **Given** una rama con una unidad que incumple, **When** se empuja, **Then** la comprobación
   termina en rojo y el informe nombra el archivo y el motivo de cada hallazgo.
3. **Given** un push que no toca ninguna unidad, **When** se ejecuta, **Then** termina en verde sin
   juzgar nada, y dice que no había nada que comprobar.
4. **Given** una rama con varias unidades tocadas, **When** se empuja, **Then** se comprueban todas y
   el resultado refleja el conjunto.

---

### User Story 2 - Sólo se juzga lo que el autor ha tocado (Priority: P1)

El registro comprueba las unidades que el push modifica, no todas las del repositorio. Un autor no
recibe hallazgos de una unidad ajena que ya estaba rota antes de que él llegara.

**Why this priority**: si el registro señalara todo, el autor aprendería a ignorarlo, y una
comprobación que se ignora no protege nada.

**Independent Test**: en un repositorio con dos unidades, una rota, tocar sólo la sana y comprobar que
el resultado es verde y no menciona la rota.

**Acceptance Scenarios**:

1. **Given** un push que toca un archivo dentro de una unidad, **When** se descubren las unidades,
   **Then** aparece esa unidad y ninguna otra.
2. **Given** un push que toca un archivo que no pertenece a ninguna unidad, **When** se descubren,
   **Then** no aparece ninguna.
3. **Given** el primer push de una rama nueva, cuando no hay un punto de comparación anterior,
   **When** se descubren, **Then** se comprueban sólo las unidades que contienen archivos del último
   commit, porque el alcance del registro es lo que el autor tocó y nunca las demás unidades del
   repositorio.
4. **Given** un push que borra una unidad entera, **When** se descubren, **Then** esa unidad no
   aparece, porque ya no hay nada que juzgar.

---

### User Story 3 - La regla que corre en la máquina y la que corre en la automatización son la misma (Priority: P1)

El validador que la automatización ejecuta viene del mismo commit del estándar del que viene el propio
workflow. No hay forma de que el autor vea verde en su máquina y la automatización vea rojo por estar
usando versiones distintas.

**Why this priority**: dos versiones del validador es el defecto que hace que nadie se fíe de la
comprobación. Y arreglarlo después, cuando ya hay unidades publicadas, es una migración.

**Independent Test**: ejecutar el registro y comprobar en su informe que la versión del validador
corresponde al commit del workflow.

**Acceptance Scenarios**:

1. **Given** una ejecución del registro, **When** se instala el validador, **Then** se instala desde
   el mismo commit del estándar que provee el workflow, sin que nadie tenga que teclear una versión.
2. **Given** un repositorio del estándar que no sea público, **When** el llamador facilita una
   credencial de lectura, **Then** la instalación funciona igual.

---

### User Story 4 - El dominio invoca sin saber cómo funciona (Priority: P2)

El repositorio de dominio tiene un archivo corto que dice cuándo se registra y a quién llama. No
contiene lógica: si el estándar cambia lo que comprueba, el dominio no se entera y no tiene que tocar
nada.

**Why this priority**: es lo que permite que un dominio nuevo se dé de alta copiando cuatro archivos, y
lo que evita que cada dominio acabe con su propia versión de las reglas.

**Independent Test**: leer el archivo del dominio y comprobar que no contiene ninguna comprobación,
sólo el disparador, los permisos y la referencia.

**Acceptance Scenarios**:

1. **Given** el archivo del dominio, **When** se lee, **Then** declara el evento, los permisos
   mínimos y la referencia al reutilizable, y nada más.
2. **Given** un push a la rama principal, **When** se evalúa el disparador, **Then** el registro no se
   ejecuta, porque ahí manda la verificación de la solicitud de cambio.
3. **Given** la comprobación que aparece en la interfaz, **When** se lee su nombre, **Then** es el que
   el diseño fija, y no satisface por sí sola ninguna de las comprobaciones requeridas para fusionar.

---

### Edge Cases

- Un push que sólo toca documentación o configuración del repositorio no encuentra unidades y termina
  en verde diciendo que no había nada que comprobar.
- Una unidad dentro de otra no debería existir, y si existe, el descubrimiento elige la más cercana al
  archivo cambiado; el validador ya señala la anidación como error.
- Un archivo cambiado que estaba en una unidad y ya no existe no arrastra a esa unidad si la unidad
  entera desapareció.
- Si la instalación del validador falla, la comprobación termina en rojo con el motivo, nunca en verde.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El estándar MUST publicar un workflow reutilizable que aplique las reglas de la unidad a
  lo que un push toca.
- **FR-002**: El repositorio de dominio MUST tener un llamador que se dispare en cada push a una rama
  distinta de la principal, y MUST NOT dispararse en la principal.
- **FR-003**: El llamador MUST NOT contener lógica de comprobación: sólo evento, permisos y
  referencia.
- **FR-004**: El nombre de la comprobación que aparece en la interfaz MUST ser el que fija el diseño.
- **FR-005**: El registro MUST descubrir las unidades que el push toca comparando con el estado
  anterior, y MUST comprobar sólo ésas.
- **FR-006**: Cuando no haya estado anterior con el que comparar, el registro MUST comprobar sólo las
  unidades que contienen archivos del último commit, y MUST NOT comprobar las demás. Si tampoco se
  puede leer el último commit, MUST decirlo y terminar como no comprobable.
- **FR-007**: El registro MUST instalar el validador desde el mismo commit del estándar del que
  procede el workflow, sin que nadie declare una versión a mano.
- **FR-008**: El registro MUST admitir una credencial opcional de lectura sobre el estándar, para
  cuando el repositorio no sea público.
- **FR-009**: El registro MUST terminar en rojo si cualquier unidad comprobada tiene errores, y en
  verde si ninguna los tiene.
- **FR-010**: El registro MUST dejar en el resumen de la ejecución qué unidades comprobó y qué
  encontró en cada una.
- **FR-011**: Ningún paso del registro MUST poder terminar en verde sin haber hecho su trabajo.
- **FR-012**: El descubrimiento de unidades MUST ser un programa con sus propias pruebas, no un guion
  incrustado en el workflow.
- **FR-013**: El registro MUST NOT escribir en el repositorio, ni etiquetar, ni abrir incidencias, ni
  hablar con el catálogo: es sólo una comprobación.

### Key Entities

- **Unidad tocada**: la carpeta publicable más cercana a un archivo que el push cambió.
- **Registro**: la ejecución que aplica las reglas a esas unidades.
- **Llamador**: el archivo del dominio que dice cuándo y a quién.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un push a una rama de trabajo con una unidad hecha de las plantillas termina en verde.
- **SC-002**: Estropear esa unidad y volver a empujar termina en rojo, con el archivo y el motivo en
  el informe.
- **SC-003**: El descubrimiento de unidades tiene pruebas de cada caso, incluidos el primer push y el
  borrado de una unidad.
- **SC-004**: El archivo del dominio no contiene ninguna comprobación.
- **SC-005**: La instalación del validador desde el repositorio del estándar funciona también en la
  máquina del autor, en PowerShell.

## Assumptions

- El registro no habla con el catálogo de metadata: eso llega cuando el catálogo entre en alcance.
- El registro no exige aprobadores ni compara versiones con la rama principal: son reglas del cambio y
  viven en la verificación de la solicitud, que es un hito posterior.
- La comprobación del registro no satisface las comprobaciones requeridas para fusionar. Son cosas
  distintas a propósito: el registro acompaña mientras se trabaja, la verificación decide si se
  fusiona.
- El repositorio de dominio no podrá fusionar a su rama principal hasta que exista la verificación,
  porque su protección exige tres comprobaciones que todavía nadie emite. La evidencia de este hito se
  toma en la rama de trabajo, que es exactamente donde el flujo 1 ocurre.

## Clarifications

### Session 2026-09-07

- Q: ¿Cómo se fija la versión del validador que instala la automatización? → A: del mismo commit del
  estándar que provee el workflow. Nadie teclea una versión, así que no pueden separarse.
- Q: ¿El descubrimiento de unidades va en el workflow o en un programa aparte? → A: en un programa con
  pruebas. Un guion incrustado no se puede probar y esta es justo la clase de lógica que se rompe en
  silencio.
- Q: ¿Qué pasa en el primer push de una rama, cuando no hay con qué comparar? → A: el alcance son los
  archivos del último commit. **Corregido el 8 de septiembre de 2026**: la primera respuesta fue
  comprobar todas las unidades, con el argumento de que callar es peor que comprobar de más. Es la
  disyuntiva equivocada: comprobar de más le atribuye al autor los hallazgos de código que no ha
  escrito, y hay un tercer camino que no calla, que es el último commit. Si tampoco se puede leer, eso
  ya no es que falte una referencia, sino que git no responde, y entonces sí se dice y no se juzga.
- Q: ¿El registro puede fusionar o etiquetar? → A: no. Es sólo una comprobación y no escribe nada.
