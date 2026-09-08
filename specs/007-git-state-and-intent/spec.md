# Feature Specification: Estado de git, herramientas e intención pendiente

**Feature Branch**: `feat/007-git-state-and-intent`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `001-git-state-and-intent` del hito A1 del plan del asistente. Aquí es la spec 007
porque la numeración de este repositorio es secuencial.

**Input**: `REGLAS-RAMA-DE-TRABAJO.md` §2 a §5, el banco de pruebas `pruebas-rama/` con sus seis
escenarios y sus dos prototipos, y `PLAN-DE-TRABAJO-ASISTENTE-AUTORIA` §1.4 para el contrato de salida.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El asistente no toca el trabajo de nadie (Priority: P1)

Quien invoca al asistente con cambios a medias, en una rama con otro nombre, o con el repositorio en
un estado raro, recibe un mensaje que dice exactamente qué corregir. El asistente no guarda nada, no
descarta nada y no cambia de rama. Se detiene antes de preguntar y antes de escribir.

**Why this priority**: es el principio del que cuelga todo. Un asistente que descarta trabajo sin
confirmar se desinstala el mismo día y no vuelve.

**Independent Test**: dejar el repositorio en cada uno de los seis estados del banco de pruebas y
comprobar que el estado clasificado es el esperado y que no se ejecutó ninguna escritura.

**Acceptance Scenarios**:

1. **Given** un repositorio en la rama principal y sin cambios pendientes, **When** se clasifica,
   **Then** el estado dice que se puede seguir y enumera las unidades que hay.
2. **Given** una rama de trabajo bien nombrada y sin cambios pendientes, **When** se clasifica,
   **Then** el estado dice que se retoma, y nombra la acción y la unidad que la rama declara.
3. **Given** cambios sin guardar en cualquier rama, **When** se clasifica, **Then** el estado lo dice
   y el mensaje ofrece las dos salidas: guardar el trabajo o apartarlo.
4. **Given** una rama que no sigue la forma esperada, **When** se clasifica, **Then** el mensaje dice
   cómo volver a la rama principal o cómo renombrarla.
5. **Given** una rama bien formada que nombra una unidad que no existe, **When** se clasifica,
   **Then** el mensaje lo dice y enumera las unidades que sí hay.
6. **Given** un repositorio con una operación a medias, sin origen, o con la cabeza suelta, **When**
   se clasifica, **Then** el estado dice que está bloqueado y por cuál de esas razones.

---

### User Story 2 - El nombre de la rama es información, no decoración (Priority: P1)

Cuando el autor ya está en una rama de trabajo, el asistente deduce de su nombre qué se está haciendo
y sobre qué unidad, y no vuelve a preguntarlo. Retomar deja de ser un interrogatorio.

**Why this priority**: es lo que hace que retomar sea barato, y retomar es la mitad del trabajo real
de autoría.

**Independent Test**: para cada prefijo válido, comprobar que la acción y la unidad se leen del
nombre; para nombres inválidos, que se rechazan.

**Acceptance Scenarios**:

1. **Given** una rama con cada uno de los tres prefijos válidos, **When** se clasifica, **Then** la
   acción corresponde al prefijo y la unidad al resto del nombre.
2. **Given** una rama cuyo nombre de unidad no cumple la forma esperada, **When** se clasifica,
   **Then** se trata como una rama desconocida.
3. **Given** una rama de creación que nombra una unidad que todavía no existe, **When** se clasifica,
   **Then** se acepta, porque es la que se está creando.
4. **Given** una rama de modificación o de obsolescencia que nombra una unidad inexistente, **When**
   se clasifica, **Then** se rechaza.

---

### User Story 3 - Un trabajo interrumpido se retoma sin volver a preguntarlo todo (Priority: P1)

Cuando el asistente se detiene porque el repositorio no está listo, recuerda lo que el autor ya había
elegido. Al volver, lo propone en vez de preguntarlo otra vez. La memoria sobrevive a cerrar la
sesión, porque vive en el repositorio y no en la conversación.

**Why this priority**: es la diferencia entre detenerse y perder el trabajo hecho hasta ahí. Y hace
cumplible el principio de releer en vez de recordar.

**Independent Test**: guardar una intención, comprobar que se lee en una invocación nueva, y que se
borra cuando se completa.

**Acceptance Scenarios**:

1. **Given** una intención guardada, **When** se lee en una sesión nueva, **Then** aparece con su
   acción y su unidad.
2. **Given** una intención guardada, **When** se borra, **Then** deja de aparecer.
3. **Given** una intención con acción pero sin unidad, **When** se lee, **Then** consta como
   pendiente, porque el autor eligió qué hacer aunque no sobre qué.
4. **Given** un repositorio sin intención guardada, **When** se lee, **Then** consta que no hay nada
   pendiente.
5. **Given** una intención guardada con un valor que no es ninguna de las tres acciones, **When** se
   lee, **Then** no se da por buena y se dice por qué.
6. **Given** una copia nueva del repositorio, **When** se lee, **Then** no hay intención, porque la
   memoria vive en la copia y no viaja.

---

### User Story 4 - El asistente comprueba sus herramientas antes de prometer nada (Priority: P2)

Antes de la primera pregunta, el asistente comprueba que la máquina tiene lo que necesita. Si falta
algo, lo dice con la instrucción exacta, igual que hace con un estado de git que no acepta.

**Why this priority**: fallar a mitad del diálogo, cuando el autor ya ha contestado cinco preguntas,
es peor que no empezar.

**Independent Test**: simular la ausencia de cada herramienta y comprobar que se nombra la que falta.

**Acceptance Scenarios**:

1. **Given** una máquina con todo lo necesario, **When** se comprueba, **Then** el resultado dice que
   se puede seguir.
2. **Given** una herramienta ausente, **When** se comprueba, **Then** el resultado la nombra y dice
   qué hacer.
3. **Given** una versión del lenguaje por debajo del mínimo, **When** se comprueba, **Then** se
   señala igual que una ausencia.
4. **Given** la herramienta de la plataforma sin sesión activa, **When** se comprueba, **Then** se
   señala, porque estar instalada no basta.

---

### Edge Cases

- La rama principal por detrás de su origen no detiene nada, pero se avisa: el asistente parte del
  origen y el autor debe saberlo.
- Una rama de trabajo por detrás de la principal se avisa y no se toca: reordenar el historial es del
  autor.
- Un manifiesto de unidad ilegible no puede desaparecer en silencio, porque haría que su unidad no
  apareciera y el asistente diría que no existe.
- Los avisos de retraso se calculan con lo que hay en la copia local. Si nadie ha traído novedades
  desde el origen, el aviso refleja la última vez que se trajeron, y eso se dice.
- La memoria de la intención se comparte entre árboles de trabajo del mismo repositorio, porque vive
  donde vive la configuración local.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El asistente MUST clasificar el estado del repositorio en uno de seis, con los nombres
  que el diseño fija, y MUST NOT modificar nada al hacerlo.
- **FR-002**: La clasificación MUST acompañar cada estado con lo que el diálogo necesita: la lista de
  unidades cuando se puede seguir, y la acción y la unidad cuando se retoma.
- **FR-003**: Cada estado de parada MUST llevar un mensaje que diga qué corregir y con qué comando.
- **FR-004**: La forma del nombre de rama MUST ser la que el diseño fija, y una rama de creación MUST
  admitir una unidad que todavía no existe.
- **FR-005**: La clasificación MUST avisar cuando la rama principal está por detrás de su origen, y
  cuando una rama de trabajo está por detrás de la principal, sin detenerse por ello.
- **FR-006**: La lista de unidades MUST salir de los manifiestos del repositorio, y un manifiesto
  ilegible MUST constar en la salida en lugar de ignorarse en silencio.
- **FR-007**: La intención pendiente MUST guardarse en el repositorio de forma que sobreviva a cerrar
  la sesión y MUST NOT ensuciar el árbol de trabajo ni versionarse.
- **FR-008**: Se MUST poder leer, guardar y borrar la intención, y las tres operaciones MUST devolver
  el estado resultante.
- **FR-009**: Una intención con una acción que no es de las válidas MUST NOT darse por buena, y MUST
  decirse por qué.
- **FR-010**: La comprobación de herramientas MUST cubrir el intérprete con su versión mínima, el
  control de versiones y la herramienta de la plataforma con sesión activa, y MUST nombrar lo que
  falte.
- **FR-011**: Cada script MUST imprimir un solo documento estructurado en la salida estándar y el
  diagnóstico en la de error.
- **FR-012**: Cada script MUST terminar con éxito cuando ha podido clasificar, aunque el resultado sea
  de parada, y sólo con error cuando no ha podido ejecutar.
- **FR-013**: Las reglas MUST poder probarse con datos, sin repositorio y sin red.
- **FR-014**: Los scripts MUST funcionar sin instalar nada y MUST usar sólo la biblioteca estándar.

### Key Entities

- **Estado del repositorio**: uno de seis, con lo que cada uno lleva consigo.
- **Rama de trabajo**: una acción y una unidad codificadas en un nombre.
- **Intención pendiente**: lo que el autor ya eligió y todavía no se ha completado.
- **Comprobación de herramientas**: qué hace falta en la máquina y qué falta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los seis escenarios del banco de pruebas dan el estado esperado, comprobado sin red.
- **SC-002**: Guardar una intención, detenerse y volver la recupera; completarla la borra.
- **SC-003**: Las reglas se prueban con datos y sin repositorio; sólo los adaptadores necesitan uno.
- **SC-004**: Los scripts se ejecutan también desde la consola de Windows.
- **SC-005**: Ningún script escribe en el repositorio salvo la memoria de la intención.

## Assumptions

- Crear la rama no entra aquí: esta capacidad clasifica y recuerda, no actúa. Quien crea la rama es el
  diálogo, con lo que esta capacidad le dice.
- La preparación del entorno privado del validador no entra en la comprobación de herramientas: mirar
  qué hay en la máquina y crear un entorno con red son dos responsabilidades distintas, y la segunda
  llega con la capacidad que la necesita.
- Los avisos de retraso usan lo que hay en la copia local, sin traer novedades del origen. Traerlas
  sería una escritura, y aquí no se escribe.

## Clarifications

### Session 2026-09-07

Los documentos fijan los estados, la forma de la rama y las claves de la memoria. No fijan el resto,
y esto es lo decidido.

- Q: ¿Qué devuelve la comprobación de herramientas y qué estados tiene? → A: dos, uno de que se puede
  seguir y otro de que falta algo, y en el segundo se nombra qué falta y qué hacer. La creación del
  entorno del validador queda fuera, por ser otra responsabilidad.
- Q: ¿En qué orden se ejecutan los tres scripts? → A: herramientas, intención y estado de git. Es lo
  que dice el plan, y es el orden que evita preguntar antes de saber si se puede.
- Q: ¿Qué código de salida usa un estado de parada? → A: el de éxito. Detenerse es un resultado, no un
  fallo. Sólo no poder ejecutar es un fallo. Los prototipos no lo cumplen y se corrige al portarlos.
- Q: ¿Dónde va el diagnóstico? → A: a la salida de error, y la salida estándar lleva sólo el documento
  estructurado. Los prototipos tampoco lo cumplen.
- Q: ¿Cómo se exponen los avisos de retraso que las reglas exigen? → A: como campos de la
  clasificación. Hoy las reglas los piden y ningún campo los lleva, así que nadie podría avisarlos.
- Q: ¿Qué pasa con un manifiesto ilegible? → A: consta en la salida. Ignorarlo en silencio haría que
  su unidad no apareciera y que el asistente dijera que no existe, que es el peor mensaje posible.
- Q: ¿Y una intención con un valor corrupto? → A: no se da por buena y se dice por qué. Darla por
  buena llevaría el diálogo por un camino que el autor no eligió.
