# Feature Specification: El asistente de autoría existe como unidad publicable

**Feature Branch**: `feat/006-authoring-assistant-setup`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: el hito A0 del PLAN-DE-TRABAJO-ASISTENTE-AUTORIA, que es el hito 2 del plan global.
La numeración de `specs/` es la secuencial de este repositorio y no la del plan del asistente: sus
specs `001` a `00N` empiezan aquí en la `007`.

**Input**: PLAN-DE-TRABAJO-ASISTENTE-AUTORIA §1.4 (estructura del plugin y para quién es cada regla) y
§1.5 (cómo llega el código a la máquina del autor).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El asistente existe y se puede instalar antes de hacer nada (Priority: P1)

Quien va a construir el asistente necesita que el plugin exista, se instale en los dos clientes y
aparezca listado, antes de escribir una sola regla. Así lo que se mida sobre la forma se mide con el
esqueleto y no cuando ya hay trece scripts escritos contra la forma equivocada.

**Why this priority**: es el punto de decisión del hito. Si un cliente no acepta esta forma, mover un
esqueleto cuesta una tarde y mover el asistente entero cuesta el hito.

**Independent Test**: instalar el plugin desde este repositorio en Copilot CLI y en Claude Code, y
comprobar que aparece listado con su nombre y su descripción.

**Acceptance Scenarios**:

1. **Given** el plugin sin contenido, **When** se instala en cada cliente, **Then** aparece listado
   con el nombre y la descripción que declara.
2. **Given** el plugin instalado, **When** se pide su skill, **Then** el cliente lo encuentra por el
   nombre del directorio.
3. **Given** el manifiesto en la ruta que el estándar fija, **When** lo lee cada cliente, **Then**
   ninguno de los dos lo rechaza.

---

### User Story 2 - El asistente se gobierna con las reglas que él mismo publica (Priority: P1)

El plugin del equipo de plataforma pasa por el mismo validador que cualquier unidad de un dominio, sin
excepciones ni exenciones. Si publicar exigiera algo que la unidad del propio equipo no cumple, la
exigencia sería del papel y no del sistema.

**Why this priority**: es la prueba más barata de que el estándar sirve, y la más difícil de recuperar
si se pierde. Una exención concedida al principio no se retira nunca.

**Independent Test**: pasar el validador sobre el plugin y comprobar que no hay errores, y que los
avisos son exactamente los que se esperan.

**Acceptance Scenarios**:

1. **Given** el plugin, **When** se le aplican las reglas del estándar, **Then** no hay ningún error.
2. **Given** un aviso que hoy es correcto, **When** deja de aparecer, **Then** la comprobación lo nota
   y obliga a retirar la excepción en lugar de dejarla viva.
3. **Given** un cambio que rompa el gobierno del plugin, **When** se ejecuta la comprobación,
   **Then** falla antes de llegar a la solicitud de cambio.

---

### User Story 3 - El autor no instala nada para tener el asistente (Priority: P1)

Quien usa el asistente clona el plugin con su cliente y funciona. No ejecuta gestores de paquetes, no
crea entornos y no arrastra dependencias. La única instalación que ocurre alguna vez es la del
validador del estándar, y la hace el propio asistente en un entorno propio la primera vez.

**Why this priority**: es la promesa que hace usable la herramienta en una organización donde pedir
permisos cuesta semanas. Se rompe con añadir una sola dependencia, y sin una comprobación nadie se
entera hasta que falla en la máquina de otro.

**Independent Test**: comprobar que el núcleo se importa como lo hará el autor y que no usa nada fuera
de la biblioteca estándar.

**Acceptance Scenarios**:

1. **Given** el núcleo, **When** se importa como lo hacen los scripts del plugin, **Then** funciona
   sin instalar nada.
2. **Given** cualquier módulo del núcleo, **When** se leen sus importaciones, **Then** ninguna sale de
   la biblioteca estándar.
3. **Given** el núcleo, **When** se lee su nombre, **Then** no puede chocar con el de otro plugin
   instalado en la misma sesión.

---

### User Story 4 - Está fijado contra qué versión del estándar valida el autor (Priority: P2)

El plugin declara qué versión del validador instala, por etiqueta y por commit. Así el autor y la
automatización aplican las mismas reglas, y mover una referencia movible no cambia en silencio lo que
alguien tiene instalado.

**Why this priority**: dos versiones del validador es lo que hace que nadie se fíe de la comprobación
local. Y es barato ahora y caro después.

**Independent Test**: leer la declaración y comprobar que la etiqueta y el commit se corresponden con
una versión publicada del estándar.

**Acceptance Scenarios**:

1. **Given** la declaración del plugin, **When** se lee, **Then** nombra una etiqueta de versión
   concreta y su commit.
2. **Given** una etiqueta de versión concreta, **When** el estándar publica algo nuevo, **Then** esa
   etiqueta no se mueve; sólo la referencia mayor movible se mueve.

---

### Edge Cases

- El plugin todavía no tiene suite de evaluación, así que el validador avisa. Es correcto: no hay nada
  que evaluar hasta que el skill tenga contenido, y la suite se exige para publicar, no para existir.
- El cálculo automático de riesgo no ve que el asistente ejecuta código propio, porque lo hace sin
  hooks ni servidor. El autor lo eleva a mano, que es para lo que existe ese campo.
- Las carpetas que el diseño dibuja y todavía no tienen contenido no se crean vacías: una carpeta con
  un archivo de relleno es un recurso huérfano y el propio validador lo avisaría.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El repositorio del estándar MUST contener el asistente como una unidad publicable, con
  su identidad y su gobierno propios.
- **FR-002**: El asistente MUST pasar las reglas del estándar sin ningún error.
- **FR-003**: El repositorio MUST comprobar en cada cambio que sus propias unidades cumplen sus
  reglas, y que sus avisos son exactamente los declarados como esperados.
- **FR-004**: El núcleo del asistente MUST poder importarse sin instalar nada, del mismo modo en que
  lo harán sus scripts.
- **FR-005**: El núcleo MUST usar sólo la biblioteca estándar del lenguaje.
- **FR-006**: El nombre del núcleo MUST ser distinto del nombre del plugin y MUST NOT poder chocar con
  el de otro plugin instalado en la misma sesión.
- **FR-007**: El núcleo MUST estar organizado en las capas que el diseño fija, y cada capa MUST
  declarar de qué se hace cargo.
- **FR-008**: La capa de reglas puras MUST NOT hablar con el exterior ni importar las demás capas.
- **FR-009**: El plugin MUST declarar contra qué versión del validador del estándar trabaja, por
  etiqueta y por commit.
- **FR-010**: El gobierno del asistente MUST declarar los ejecutables que usa, aunque ninguna regla
  automática pueda contrastarlos en un skill.
- **FR-011**: El gobierno del asistente MUST declarar un nivel de riesgo acorde con lo que hace,
  elevándolo por encima del mínimo que el cálculo automático deriva.
- **FR-012**: Las pruebas del plugin MUST viajar con la unidad y MUST ejecutarse también en la
  integración continua del repositorio.
- **FR-013**: El asistente MUST NOT hacer nada todavía: el núcleo determinístico y el diálogo son las
  specs siguientes.

### Key Entities

- **Plugin del asistente**: la unidad publicable, con su envoltorio y su contenido.
- **Núcleo**: el paquete que los scripts importan, organizado en capas.
- **Anclaje del validador**: la declaración de contra qué versión del estándar valida el autor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El validador del estándar no encuentra ningún error en el asistente, y sus avisos son
  exactamente los esperados.
- **SC-002**: El plugin se instala y aparece listado en los dos clientes.
- **SC-003**: El núcleo se importa sin instalar nada y no usa ninguna dependencia externa.
- **SC-004**: La etiqueta que el plugin ancla corresponde a un estado publicado del estándar.

## Assumptions

- El asistente no hace nada en esta spec. Es deliberado: la forma se mide con el esqueleto, cuando
  cambiarla todavía es barato.
- Las carpetas de referencias y de scripts llegan con las specs que las llenan.
- El nivel de riesgo declarado es el que corresponde a una herramienta que ejecuta código propio y que
  escribirá en los repositorios de todos los dominios, y añade a Ciberseguridad como aprobador.

## Clarifications

### Session 2026-09-07

- Q: ¿El núcleo puede llamarse igual que el plugin? → A: no. Son dos cosas distintas y el nombre debe
  decirlo, y además el núcleo se importa por el camino de búsqueda del lenguaje, así que dos plugins
  con un paquete del mismo nombre se pisarían en la misma sesión.
- Q: ¿Los permisos pueden ir vacíos mientras el plugin no haga nada? → A: no. El gobierno declara lo
  que la unidad usa, y ninguna regla automática puede contrastarlo en un skill: si no lo declara quien
  lo escribe, no lo declara nadie.
- Q: ¿Se deja el riesgo en el mínimo que calcula la automatización? → A: no. El cálculo no ve que el
  asistente ejecuta código propio porque lo hace sin hooks ni servidor. Elevarlo es exactamente para
  lo que existe ese campo, y añade el aprobador que corresponde.
- Q: ¿Se crea ya el árbol completo que dibuja el diseño? → A: no. Una carpeta con un archivo de
  relleno es un recurso huérfano, y el propio validador lo avisaría. Cada carpeta llega con su spec.
