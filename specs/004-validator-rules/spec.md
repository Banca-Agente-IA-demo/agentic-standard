# Feature Specification: El validador del estándar y su comando de reglas

**Feature Branch**: `feat/004-validator-rules`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `std-003-validator-rules` del PLAN-GLOBAL §5, hito 1.

**Depende de**: las specs 002 (esquemas) y 003 (plantillas), ya fusionadas.

**Input**: `REVISION-ESQUEMAS-HITO-1.md` §7.1 (tabla completa de reglas de la unidad, con el origen de
cada una) y §5 (qué se lee de cada formato sin esquema propio); decisiones D1 a D7; lineamiento 03 §1
(cálculo de riesgo) y §3 (matriz de controles por tipo); 04 §4 (árbol de la unidad).

**Revisado el 2026-09-07**: la primera redacción salió de §5, que es un subconjunto. La sección 7.1
apareció después con la tabla completa y se cotejó regla a regla. Lo que faltaba se añadió; lo que no
se puede hacer sin salir del árbol se documenta abajo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El autor sabe si su unidad cumple el estándar antes de pedir revisión (Priority: P1)

Quien está creando o modificando una unidad ejecuta un comando sobre la carpeta de esa unidad y
obtiene la lista de lo que incumple, con el archivo y el motivo de cada hallazgo, o la confirmación de
que cumple. El mismo comando lo ejecuta la automatización en cada push, sin diferencias.

**Why this priority**: es la razón de ser de la capacidad. El asistente de autoría del hito 2 lo
invoca y lee su resultado; sin él no hay nada que enseñar al autor ni que exigir en la solicitud de
cambio.

**Independent Test**: ejecutar el comando sobre una unidad instanciada de las plantillas: cumple.
Estropear un archivo de una forma concreta: señala ese archivo y ese motivo.

**Acceptance Scenarios**:

1. **Given** una unidad bien formada, **When** se ejecuta el comando sobre su carpeta, **Then** no
   hay hallazgos y el resultado dice que cumple.
2. **Given** una unidad con varios incumplimientos, **When** se ejecuta el comando, **Then** los
   lista todos, no sólo el primero, cada uno con su archivo y su motivo.
3. **Given** una carpeta que no es una unidad publicable, **When** se ejecuta el comando, **Then**
   dice que falta el envoltorio y no intenta juzgar el contenido.
4. **Given** cualquier ejecución, **When** termina, **Then** deja un indicador que otro proceso puede
   consumir sin leer el informe.

---

### User Story 2 - Lo declarado y lo que hay en el árbol no pueden divergir (Priority: P1)

El control de permisos mínimos sólo vale si alguien compara la declaración con los hechos. La unidad
declara qué herramientas, qué comandos y qué servidor usa; el validador lo contrasta con lo que
realmente aparece en los agentes, en los hooks y en la configuración de servidor.

**Why this priority**: es el control C1, el que sostiene el resto. Una declaración que nadie contrasta
es documentación, no gobierno.

**Independent Test**: por cada pareja declaración/hecho, un caso que cumple y uno que no.

**Acceptance Scenarios**:

1. **Given** un agente que usa una herramienta no declarada en los permisos de la unidad, **When** se
   valida, **Then** falla nombrando la herramienta y el agente.
2. **Given** un hook que invoca un ejecutable no declarado, **When** se valida, **Then** falla
   nombrando el ejecutable.
3. **Given** una unidad cuya configuración de servidor declara un servidor que no está en los
   permisos, o al revés, **When** se valida, **Then** falla.
4. **Given** una unidad con configuración de servidor pero sin su bloque de gobierno, o con el bloque
   pero sin configuración, **When** se valida, **Then** falla.
5. **Given** una unidad cuya configuración usa una credencial que el gobierno no declara, o declara
   una que la configuración no usa, **When** se valida, **Then** falla en los dos sentidos.
6. **Given** una unidad con más de un servidor, **When** se valida, **Then** falla.

---

### User Story 3 - La identidad y la versión son consistentes en todo el árbol (Priority: P1)

El nombre por el que se instala, la mitad del identificador de gobierno, el nombre del directorio y la
versión que copiará el índice tienen que decir lo mismo. Si divergen, la publicación instala otra cosa
o la etiqueta no corresponde al contenido.

**Why this priority**: la versión y el nombre viajan a la etiqueta, al índice y a la ficha del
catálogo. Un desajuste aquí se propaga a todo lo demás y sólo se descubre al instalar.

**Independent Test**: alterar cada pieza de la identidad por separado y comprobar que cada alteración
produce su propio hallazgo.

**Acceptance Scenarios**:

1. **Given** una unidad cuyo identificador de gobierno no termina en el nombre de su archivo de
   identidad, **When** se valida, **Then** falla.
2. **Given** una unidad cuyo identificador de gobierno no empieza por el repositorio que la aloja,
   **When** se valida, **Then** falla.
3. **Given** una versión que no es estrictamente conforme al formato de versionado, **When** se
   valida, **Then** falla.
4. **Given** un archivo de identidad con un campo fuera de los que el formato permite, **When** se
   valida, **Then** falla.
5. **Given** un artefacto de texto cuyo nombre declarado no coincide con el de su archivo o
   directorio, **When** se valida, **Then** falla.

---

### User Story 4 - El riesgo declarado nunca queda por debajo de los hechos (Priority: P2)

El nivel de riesgo mínimo se calcula de hechos: si la unidad escribe fuera del cliente, si maneja
credenciales, si ejecuta código propio sin que nadie lo invoque, y de la clasificación del dato. El
autor puede elevarlo, nunca bajarlo.

**Why this priority**: el nivel decide quién más aprueba y cuánto dura esa aprobación. Un nivel por
debajo de los hechos salta aprobadores obligatorios.

**Independent Test**: construir unidades con cada combinación de hechos y comprobar el mínimo
calculado; declarar por debajo y comprobar que falla; declarar por encima y comprobar que pasa.

**Acceptance Scenarios**:

1. **Given** una unidad con un servidor que escribe fuera del cliente, con credenciales declaradas, o
   con la clasificación de dato más sensible, **When** se calcula el riesgo, **Then** el mínimo es el
   nivel más alto.
2. **Given** una unidad que ejecuta código propio sin invocación, o que usa un servidor sólo de
   lectura, **When** se calcula, **Then** el mínimo es el nivel intermedio.
3. **Given** una unidad sin ninguno de esos hechos, **When** se calcula, **Then** el mínimo es el
   nivel más bajo.
4. **Given** una unidad que declara un nivel inferior al calculado, **When** se valida, **Then**
   falla mostrando el calculado y el declarado.
5. **Given** una unidad que declara un nivel superior al calculado, **When** se valida, **Then**
   pasa, porque elevar es una decisión del autor.

---

### User Story 5 - Las reglas de portabilidad medidas se hacen exigibles (Priority: P2)

Lo que se midió en los dos clientes deja de ser una nota en un documento y pasa a ser una regla: los
eventos que disparan en ambos, las dos grafías con las que un agente restringe su servidor, el tope de
tiempo de cada hook y que su comando apunte dentro de la unidad.

**Why this priority**: son los defectos que no fallan de forma visible. Un evento mal escrito no da
error, simplemente no dispara nunca; una sola grafía deja al agente sin servidor en un cliente y sin
aviso en el otro.

**Independent Test**: por cada regla medida, un caso que cumple y uno que no.

**Acceptance Scenarios**:

1. **Given** unos hooks con un evento fuera de la lista portable, **When** se valida, **Then** avisa
   sin bloquear, porque la lista todavía no está fijada en el lineamiento.
2. **Given** una acción de hook sin tope de tiempo, o con el nombre de campo que la demo anterior
   aceptaba, **When** se valida, **Then** falla.
3. **Given** un comando de hook que apunta fuera de la unidad, o que descarga algo en ejecución,
   **When** se valida, **Then** falla.
4. **Given** un agente que restringe su servidor con una sola de las dos grafías, **When** se valida,
   **Then** falla nombrando la que falta.
5. **Given** un agente que no restringe herramientas en una unidad que lleva servidor, **When** se
   valida, **Then** avisa, porque hereda todo lo instalado en la sesión.

---

### User Story 6 - El validador se instala desde el repositorio del estándar (Priority: P1)

La automatización y la máquina del autor instalan la misma versión del validador desde el repositorio
del estándar, fijada por etiqueta, y con el contrato de gobierno viajando dentro. No hay dos copias
del esquema que puedan separarse.

**Why this priority**: si el validador de la máquina y el de la automatización difieren, el autor ve
verde y la solicitud de cambio ve rojo. Y si el esquema viaja aparte, deriva.

**Independent Test**: construir el paquete y comprobar que el contrato de gobierno está dentro y es el
mismo del repositorio; instalarlo en un entorno limpio y ejecutar el comando.

**Acceptance Scenarios**:

1. **Given** el paquete construido, **When** se inspecciona, **Then** contiene el contrato de
   gobierno del repositorio, sin diferencias.
2. **Given** un entorno limpio, **When** se instala el paquete desde el repositorio y se ejecuta el
   comando, **Then** funciona sin más dependencias que las que el paquete declara.

---

### Edge Cases

- Una unidad sin artefactos de texto, sólo con configuración de servidor o sólo con hooks, es válida:
  está medido que los dos clientes las cargan. Sus permisos de herramientas pueden estar vacíos.
- Una unidad sin suite de evaluación no falla en esta capacidad: la suite se exige para publicar, y
  eso es de la automatización de verificación, no de las reglas de la unidad.
- Un archivo de gobierno con un campo desconocido ya lo rechaza el contrato; el validador no repite
  esa comprobación con reglas propias.
- Un valor literal en la configuración de servidor que parece una credencial es un hallazgo, aunque el
  nombre de la variable esté bien declarado.
- La declaración de tratamiento de contenido externo se exige según el tipo de lo que la unidad
  contiene, no siempre: una unidad que sólo expone un servidor no interpreta contenido externo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El repositorio MUST publicar un paquete instalable desde el propio repositorio, con el
  contrato de gobierno incluido como dato y sin una segunda copia del esquema que pueda derivar.
- **FR-002**: El paquete MUST exponer un comando que recibe la carpeta de una unidad y emite sus
  hallazgos.
- **FR-003**: El comando MUST recorrer todas las reglas y emitir todos los hallazgos, no detenerse en
  el primero.
- **FR-004**: Cada hallazgo MUST decir su severidad, la regla que lo produjo, el archivo al que se
  refiere y el motivo en una frase.
- **FR-005**: El comando MUST distinguir al menos dos severidades: la que impide publicar y la que
  sólo advierte.
- **FR-006**: El comando MUST terminar con un indicador consumible por otro proceso, distinto para
  cumple, no cumple y no se pudo comprobar.
- **FR-007**: El validador MUST comprobar que el archivo de gobierno valida contra su contrato.
- **FR-008**: El validador MUST comprobar la consistencia de la identidad: repositorio, nombre de la
  unidad, nombre del archivo de identidad y directorio.
- **FR-009**: El validador MUST exigir versión estrictamente conforme al formato de versionado y
  rechazar campos fuera de los que el formato de identidad permite.
- **FR-010**: El validador MUST contrastar las herramientas de cada agente, los ejecutables de cada
  hook y el servidor de la configuración con lo declarado en los permisos de la unidad.
- **FR-011**: El validador MUST exigir que la unidad lleve como mucho un servidor, que su nombre sea
  el mismo en la configuración, en el bloque de gobierno y en los permisos, y que el bloque exista si
  y sólo si existe la configuración.
- **FR-012**: El validador MUST contrastar en los dos sentidos las credenciales declaradas con las
  referenciadas por la configuración, y MUST señalar un valor literal que parezca una credencial.
- **FR-013**: El validador MUST calcular el nivel de riesgo mínimo a partir de los hechos y MUST
  fallar si el declarado es inferior.
- **FR-014**: El validador MUST exigir la declaración de tratamiento de contenido externo cuando el
  tipo de lo que la unidad contiene lo requiera.
- **FR-015**: El validador MUST comprobar sobre los hooks el tope de tiempo, la ruta del comando
  dentro de la unidad, la ausencia de descarga en ejecución y el nombre de campo correcto, y MUST
  avisar de un evento fuera de la lista portable.
- **FR-016**: El validador MUST comprobar que un agente que restringe su servidor declara las dos
  grafías, y MUST avisar si no restringe herramientas en una unidad con servidor.
- **FR-017**: El validador MUST comprobar sobre cada artefacto de texto que su nombre declarado
  coincide con el de su archivo o directorio y que su descripción no está vacía.
- **FR-018**: El validador MUST NOT juzgar nada del contenido de los formatos de cliente más allá de
  lo enumerado: la estructura interna de cada tipo la fija la herramienta.
- **FR-020**: El validador MUST comprobar que la descripción de un artefacto no supera el máximo del
  formato, porque es lo único que se carga en cada petición.
- **FR-021**: El validador MUST exigir que el tope de tiempo de cada hook esté por debajo del techo
  del estándar, y que los hooks traigan pruebas que los ejerciten.
- **FR-022**: El validador MUST comprobar que un agente que restringe su servidor lo nombra con el de
  su propia unidad, no con el de otra.
- **FR-023**: El validador MUST avisar cuando un artefacto de texto no trae su suite, sin bloquear,
  porque estas reglas corren también en el push.
- **FR-024**: El validador MUST comprobar el layout de la unidad: cada artefacto en su carpeta, sin
  unidades anidadas, y sin rutas absolutas en los archivos ejecutables o de configuración.
- **FR-025**: El archivo de identidad MUST declarar su referencia de esquema, que es pública y sí
  resuelve desde el editor.
- **FR-019**: Las reglas MUST ser comprobables con datos, sin leer disco ni red, y el paquete MUST
  tener pruebas de cada una en CI.

### Key Entities

- **Unidad**: la carpeta con su identidad y su gobierno, más los artefactos que contiene.
- **Hallazgo**: severidad, regla, archivo y motivo.
- **Informe**: la lista de hallazgos y el veredicto.
- **Nivel de riesgo**: el mínimo derivado de hechos, y el declarado por el autor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada fila de la tabla de la sección 5 de la revisión tiene al menos una regla y al menos
  una prueba.
- **SC-002**: Una unidad instanciada de las plantillas de la spec 003 pasa el validador sin hallazgos.
- **SC-003**: Estropear cualquiera de las comprobaciones produce un hallazgo que nombra el archivo y
  el motivo, en el 100 % de los casos probados.
- **SC-004**: El paquete se instala desde el repositorio en un entorno limpio y su comando responde.
- **SC-005**: El contrato de gobierno que el paquete lleva dentro es el mismo del repositorio.

## Assumptions

- Las reglas que necesitan preguntar a GitHub (que el equipo dueño exista en la organización, que los
  aprobadores del tipo y del nivel hayan revisado) no entran en esta capacidad. El validador trabaja
  sobre el árbol; lo que necesita la interfaz de GitHub es del workflow de verificación, que es
  posterior.
- La comprobación del contrato del servidor contra el servidor real tampoco entra: exige arrancarlo, y
  el estándar sólo lo hace tras confirmación explícita del autor.
- La suite de evaluación se comprueba en su forma cuando la unidad la trae, pero su ausencia no es un
  hallazgo de esta capacidad.
- El tipo de lo que la unidad contiene se deduce del árbol, no de un campo declarado.
- El nombre del repositorio que aloja la unidad se deduce de la ruta cuando no se indica.

## Clarifications

### Session 2026-09-07

- Q: ¿El validador consulta a GitHub para resolver el equipo dueño? → A: no en esta capacidad. Es una
  regla del workflow de verificación, que sí tiene sesión autenticada. El validador se queda en el
  árbol y así sus reglas se prueban con datos.
- Q: ¿Falta de suite de evaluación es un hallazgo? → A: no aquí. La suite se exige para publicar y eso
  lo comprueba la verificación de la solicitud de cambio. Si la unidad la trae, se comprueba su forma.
- Q: ¿Cómo se evita una segunda copia del contrato de gobierno dentro del paquete? → A: el paquete lo
  incluye en el momento de construirse desde el único archivo del repositorio. No se copia al árbol.
- Q: ¿Un evento de hook fuera de la lista portable bloquea? → A: avisa. La lista se fija en el
  lineamiento 04 §2 y hasta entonces bloquear sería exigir lo que la norma todavía no dice.

### Session 2026-09-07, tras cotejar con la sección 7.1

- Q: ¿La ausencia de suite es un hallazgo? → A: **sí, como aviso**, revisando la respuesta anterior.
  La tabla 7.1 la lista como regla de la unidad. Avisa en vez de bloquear porque estas reglas corren
  también en el push, cuando el autor todavía está trabajando; el bloqueo es de la verificación de la
  solicitud de cambio (02 §8.2).
- Q: ¿Cuál es el techo del tope de tiempo de un hook? → A: el lineamiento 04 §2 exige que exista un
  techo pero no fija el número. Se declara como constante nombrada del validador, con el motivo
  escrito al lado, y se confirma cuando 04 §2 lo fije.

## Fuera de alcance, con motivo

Dos reglas de la tabla 7.1 no entran en esta capacidad porque no se pueden comprobar sobre el árbol:

| Regla | Por qué no entra | Dónde debe vivir |
|---|---|---|
| El equipo dueño existe en la organización | Exige preguntar a GitHub con una sesión autenticada. Meterlo aquí haría que las reglas dejaran de probarse con datos y que el validador fallara sin red | El job de reglas de la verificación, que sí tiene sesión |
| El contrato declarado del servidor corresponde con lo que el servidor expone | Exige arrancar el servidor, y el estándar sólo lo hace tras confirmación explícita del autor | El asistente de autoría al proponer el contrato, y el reloj que vigila el cambio externo |

Las dos quedan anotadas para que nadie las dé por hechas al leer la tabla.
