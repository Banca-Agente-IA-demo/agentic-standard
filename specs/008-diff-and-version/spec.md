# Feature Specification: Clasificación del diff y salto de versión

**Feature Branch**: `feat/008-diff-and-version`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `002-diff-and-version` del hito A1 del plan del asistente. Aquí es la spec 008
porque la numeración de este repositorio es secuencial.

**Input**: `REGLAS-DE-VERSION.md` §5 a §8 con sus casos límite, el nodo V1 del árbol de decisión, y
`PLAN-DE-TRABAJO-ASISTENTE-AUTORIA` §1.4 para el contrato de salida.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El salto de versión no lo decide la memoria de nadie (Priority: P1)

Quien ha cambiado una unidad no tiene que recordar qué fila de la tabla le toca. El asistente lee el
diff acotado a la carpeta de esa unidad, lo clasifica y dice el nivel mínimo con las rutas y las claves
concretas que lo justifican. Si el autor quiere subir más, puede; bajar, no.

**Por qué es P1**: es la razón de ser del asistente. Un salto elegido a ojo es lo que produce una
versión menor que cambia permisos, y el aprobador no vuelve a mirar porque nadie le dijo que mirara.

**Prueba independiente**: se prepara un diff de cada fila de la tabla y se comprueba que sale el nivel
que la tabla dice, con el motivo que lo señala.

**Escenarios de aceptación**:

1. **Dado** un diff que toca `permissions` en el gobierno, **cuando** se clasifica, **entonces** el
   mínimo es mayor y el motivo nombra el archivo y la clave.
2. **Dado** un diff que sólo añade un skill nuevo, **cuando** se clasifica, **entonces** el mínimo es
   menor.
3. **Dado** un diff que sólo cambia texto de un artefacto que ya estaba, **cuando** se clasifica,
   **entonces** el mínimo es parche.
4. **Dado** un diff que cae en varias filas, **cuando** se clasifica, **entonces** manda la más alta y
   los motivos de todas constan.
5. **Dado** un diff vacío, **cuando** se clasifica, **entonces** el asistente dice que no hay nada que
   versionar en vez de proponer un salto.

### User Story 2 - Quitar capacidad no se cuela como una corrección menor (Priority: P1)

Quien retira un artefacto de una unidad ya publicada recibe el salto que corresponde a romper a quien
la consume, no el de un cambio de texto.

**Por qué es P1**: es el hueco que tiene hoy el contrato. La tabla cubre añadir y cambiar, y una
eliminación cae por descarte en la última fila, que es parche. Un consumidor que invoca un skill que ha
dejado de existir se entera en ejecución.

**Prueba independiente**: se prepara un diff que borra un artefacto de una unidad publicada y se
comprueba el nivel y el motivo.

**Escenarios de aceptación**:

1. **Dado** un diff que borra un skill, un agente o un comando, **cuando** se clasifica, **entonces** el
   mínimo es mayor y el motivo dice que se retira capacidad.
2. **Dado** un diff que mueve un artefacto de sitio sin cambiar su contenido, **cuando** se clasifica,
   **entonces** cuenta como una retirada y un alta, no como un cambio de texto.
3. **Dado** un diff que borra un archivo de apoyo que no es un artefacto, **cuando** se clasifica,
   **entonces** el mínimo es parche: no había capacidad que retirar.

### User Story 3 - La versión propuesta es siempre mayor que la publicada (Priority: P1)

Quien acepta el salto obtiene una versión estrictamente mayor que la última publicada, con su sufijo de
prelanzamiento, y escrita en un solo archivo.

**Por qué es P1**: una versión que no avanza deja dos contenidos distintos con el mismo nombre, y ya
ocurrió con la regla antigua.

**Prueba independiente**: se calcula la versión propuesta para cada combinación de versión actual,
última publicada y nivel, y se comprueba la precedencia.

**Escenarios de aceptación**:

1. **Dado** que no hay ninguna versión publicada, **cuando** se propone, **entonces** sale la versión
   inicial de una unidad nueva y no se ofrece menú.
2. **Dado** que la principal ya está en prelanzamiento, **cuando** el cambio es del mismo nivel o
   inferior, **entonces** sube el contador del prelanzamiento.
3. **Dado** que la principal ya está en prelanzamiento, **cuando** el cambio es de nivel superior,
   **entonces** sube el número que corresponde y el contador vuelve a empezar.
4. **Dado** un nivel elegido inferior al mínimo, **cuando** se pide aplicarlo, **entonces** se rechaza.
5. **Dado** cualquier salto, **cuando** se aplica, **entonces** la versión cambia en el manifiesto de la
   unidad y en ningún otro archivo.

### User Story 4 - Proponer y escribir son dos operaciones distintas (Priority: P2)

Quien invoca el cálculo sin pedir que se aplique no ve modificado ningún archivo.

**Por qué es P2**: el diálogo enseña la propuesta antes de que el autor elija. Si calcular ya
escribiera, el autor estaría eligiendo sobre algo ya hecho.

**Escenarios de aceptación**:

1. **Dado** el cálculo sin la orden de aplicar, **cuando** termina, **entonces** el árbol de trabajo
   está como estaba.
2. **Dado** el cálculo con la orden de aplicar, **cuando** termina, **entonces** el documento dice qué
   versión quedó escrita y en qué archivo.

### Edge Cases

- Un prelanzamiento en vuelo y una obsolescencia a la vez: manda el prelanzamiento en curso, no una
  corrección sobre la versión publicada.
- Descartar un prelanzamiento no es una versión nueva, y no es cosa de esta capacidad.
- Dos unidades tocadas en el mismo cambio: cada una lleva su diff y su cuenta.
- Un cambio que sólo toca la suite de evaluación es parche.
- El diff se acota a la carpeta de la unidad: lo que se toque fuera no cuenta para su versión.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La clasificación MUST acotar el diff a la carpeta de la unidad y MUST compararlo contra la
  rama principal del origen.
- **FR-002**: La clasificación MUST devolver el nivel mínimo con los motivos, y cada motivo MUST nombrar
  la ruta y, cuando aplique, la clave que lo justifica.
- **FR-003**: Cuando el diff cae en más de una fila de la tabla, MUST mandar la más alta y MUST constar
  el motivo de todas.
- **FR-004**: Un diff vacío MUST decirse como tal y MUST NOT proponer ningún salto.
- **FR-005**: Retirar un artefacto de una unidad publicada MUST ser el salto que corresponde a romper a
  quien la consume. Un renombrado o un movimiento MUST tratarse como una retirada más un alta.
- **FR-006**: Borrar un archivo que no es un artefacto MUST NOT elevar el salto por sí solo.
- **FR-007**: La versión propuesta MUST ser estrictamente mayor que la última publicada, con la
  precedencia que corresponde a los prelanzamientos.
- **FR-008**: La última versión publicada MUST leerse de los lanzamientos que no son borrador, y MUST
  NOT tomarse del manifiesto de la rama principal.
- **FR-009**: Sin ninguna versión publicada, la propuesta MUST ser la versión inicial de una unidad
  nueva, sin menú.
- **FR-010**: Toda versión propuesta MUST llevar sufijo de prelanzamiento, y el contador MUST subir o
  reiniciarse según el nivel del cambio frente al prelanzamiento en curso.
- **FR-011**: Un nivel elegido por debajo del mínimo MUST rechazarse.
- **FR-012**: Sin la orden de aplicar, la operación MUST NOT escribir nada.
- **FR-013**: Al aplicar, la versión MUST escribirse sólo en el manifiesto de la unidad, y el destino
  MUST estar bajo la raíz de esa unidad.
- **FR-014**: Las tres entradas de línea de órdenes MUST consumir un solo caso de uso: son tres puertas,
  no tres lecturas del diff.
- **FR-015**: Las reglas MUST poder probarse con datos, sin repositorio, sin lanzamientos y sin red.
- **FR-016**: El acceso a los lanzamientos MUST ir por un puerto con doble de prueba, porque es lo único
  de esta capacidad que necesitaría red.

### Key Entities

- **Cambio clasificado**: el nivel mínimo y los motivos que lo sostienen.
- **Motivo**: una ruta, una clave opcional y la fila de la tabla que la señala.
- **Propuesta de versión**: la actual, la última publicada, el mínimo y la resultante.
- **Lanzamiento**: una versión publicada de una unidad, con si es borrador o no.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada fila de la tabla de las reglas de versión tiene al menos una prueba que la cubre, y
  los casos límite del documento también.
- **SC-002**: La suite corre sin red y sin lanzamientos de verdad.
- **SC-003**: Calcular sin aplicar deja el árbol de trabajo intacto, comprobado sobre un repositorio.
- **SC-004**: Ninguna versión propuesta es menor o igual que la última publicada, en ninguna de las
  combinaciones probadas.

## Assumptions

- La elección del nivel y la redacción del menú son del diálogo, no de esta capacidad. Aquí sólo se
  calcula el mínimo y se valida lo que el diálogo elija.
- Promocionar una versión, que es retirar el sufijo, queda fuera: es otro cambio y otro camino.
- Descartar un prelanzamiento queda fuera: no es una versión nueva, es cambiar el estado de un
  lanzamiento.
- El estado de la unidad, que se lee también de los lanzamientos, llega en la spec siguiente. Aquí se
  usa el mismo puerto, y esa es la razón de que el puerto exista.

## Clarifications

### Session 2026-09-07

- Q: ¿Qué salto corresponde a **quitar** un artefacto de una unidad ya publicada? → A: **mayor**, y es
  un hueco del contrato que esta spec cierra. La tabla cubre tocar permisos, añadir capacidad y cambiar
  texto; una eliminación cae por descarte en la última fila, que es parche. Retirar capacidad es lo
  contrario de añadirla, y el resto de la tabla es coherente sólo si rompe a quien la consume vale al
  menos tanto como cambiar lo que la unidad puede hacer. **Pendiente de confirmar con el usuario**: si
  decide otra cosa, cambia una fila de la tabla y su prueba, no el diseño.
- Q: ¿Y un renombrado o un movimiento? → A: una retirada más un alta. El documento no los menciona, y
  tratarlos como un cambio de texto sería la vía para retirar un artefacto sin que se note.
- Q: ¿Y borrar un archivo de apoyo? → A: parche. No había capacidad que retirar, y elevar por cualquier
  borrado convertiría en mayor la limpieza de un archivo muerto.
- Q: ¿De dónde sale la última versión publicada? → A: de los lanzamientos que no son borrador, no del
  manifiesto de la rama principal, que puede ir por delante de lo publicado.
- Q: ¿Por qué un puerto aquí, si en la spec anterior no había ninguno? → A: porque los lanzamientos son
  lo único que necesita red, y sin doble de prueba la suite no podría correr sin ella. Es el único
  puerto previsto del asistente y hay que vigilar que siga siendo uno.
