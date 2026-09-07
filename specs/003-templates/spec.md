# Feature Specification: Plantillas de unidad y de artefacto

**Feature Branch**: `feat/003-templates`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `std-002-templates` del PLAN-GLOBAL §5, hito 1. La carpeta va desfasada un número
respecto al nombre del plan, porque Spec Kit numera secuencialmente y `001` fue la prueba de humo del
hito 0.

**Depende de**: la spec 002, que publica `schemas/`. Las pruebas de esta spec validan las plantillas
instanciadas contra el contrato de gobierno.

**Input**: `REVISION-ESQUEMAS-HITO-1.md` §7 (efecto en las plantillas) y el paquete de diseño
`hito-1-esquemas-y-plantillas/templates/`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quien crea una unidad parte de una plantilla que ya cumple el estándar (Priority: P1)

Un autor, o el asistente de autoría en su nombre, copia la plantilla de unidad agrupada o de unidad
individual, rellena los marcadores y obtiene una unidad que pasa el contrato de gobierno a la primera.
Cada tipo de artefacto tiene su propia plantilla, que se copia dentro de la unidad.

**Why this priority**: el asistente de autoría del hito 2 instancia estas plantillas sin mirarlas. Si
una plantilla lleva un campo retirado o le falta uno obligatorio, el defecto se multiplica por cada
unidad que se cree.

**Independent Test**: sustituir los marcadores de cada plantilla por valores de prueba y validar el
resultado contra el contrato de gobierno: pasa, y no queda ningún marcador sin sustituir.

**Acceptance Scenarios**:

1. **Given** la plantilla de unidad agrupada, **When** se instancian sus marcadores, **Then** su
   archivo de gobierno valida sin errores.
2. **Given** la plantilla de unidad individual, **When** se instancian sus marcadores, **Then** su
   archivo de gobierno valida sin errores.
3. **Given** la plantilla de unidad agrupada más el bloque de gobierno del servidor MCP pegado en
   ella, **When** se valida, **Then** pasa, porque el bloque encaja donde dice su instrucción.
4. **Given** cualquier plantilla, **When** se instancia con los valores de prueba, **Then** no queda
   ningún marcador sin sustituir.
5. **Given** la plantilla de identidad de cualquiera de las dos unidades, **When** se instancia,
   **Then** es JSON válido, su versión es SemVer estricta y no declara ningún campo fuera de los
   permitidos por el formato de plugin.

---

### User Story 2 - Las plantillas de artefacto no reintroducen el gobierno retirado (Priority: P1)

Las plantillas de la demo anterior llevaban en el frontmatter siete campos de gobierno que hoy viven
en el archivo de gobierno de la unidad, en la etiqueta o en el catálogo. Las plantillas nuevas sólo
llevan lo que el cliente lee, más el mapa de catálogo decidido en D1, que es texto a texto.

**Why this priority**: es la vía de reintroducción más probable de todo lo que la revisión retiró,
porque una plantilla se copia sin leerla.

**Independent Test**: leer el frontmatter de las tres plantillas de artefacto de texto y comprobar que
ninguna clave de gobierno aparece en su mapa de catálogo, y que todos sus valores son texto.

**Acceptance Scenarios**:

1. **Given** la plantilla de skill, de agente o de prompt, **When** se lee su frontmatter, **Then** su
   mapa de catálogo no contiene ninguna de las claves de gobierno retiradas.
2. **Given** el mismo mapa, **When** se leen sus valores, **Then** todos son texto, como exige el
   formato de la especificación de skills.
3. **Given** cualquier plantilla de artefacto, **When** se lee su frontmatter, **Then** declara el
   nombre y la descripción que el cliente necesita.

---

### User Story 3 - Las plantillas de hooks y de evals llevan incorporado lo que el estándar exige (Priority: P1)

La suite de evaluación y la configuración de hooks son los dos sitios donde el estándar impone reglas
propias, y las plantillas tienen que nacer cumpliéndolas: las tres categorías de caso con al menos una
aserción mecánica cada una, y un hook con tope de tiempo que apunta dentro de su propia unidad y usa
un evento que dispara en los dos clientes.

**Why this priority**: un hook sin tope puede colgar el cliente de quien lo instale, y un evento mal
escrito no falla, simplemente no dispara nunca, dejando al autor creyendo que su control está activo.

**Independent Test**: leer las dos plantillas y comprobar cada regla por separado.

**Acceptance Scenarios**:

1. **Given** la plantilla de suite, **When** se leen sus casos, **Then** hay al menos tres, cada uno
   declara su categoría, y están presentes las tres categorías.
2. **Given** cada caso de la plantilla de suite, **When** se leen sus aserciones, **Then** al menos
   una es mecánica y no depende de un juez.
3. **Given** la plantilla de hooks, **When** se lee cada acción, **Then** declara un tope de tiempo
   con el nombre correcto y su comando apunta dentro de la unidad.
4. **Given** la plantilla de hooks, **When** se leen sus eventos, **Then** todos están en la lista de
   los que disparan en los dos clientes con la misma grafía.

---

### Edge Cases

- El campo de tope de tiempo que la demo aceptaba durante la migración no existe en el formato y es
  error desde el primer día: la organización nace limpia.
- Una plantilla de unidad no declara el bloque del servidor MCP: es correcto, porque el bloque sólo es
  obligatorio cuando la unidad lleva configuración de servidor.
- Un marcador que aparece en una plantilla y no tiene valor de prueba hace fallar la instanciación, no
  la deja pasar en silencio.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El repositorio MUST publicar en `templates/` las plantillas de unidad agrupada, de
  unidad individual y de cada tipo de artefacto, copiadas sin modificación del paquete de diseño.
- **FR-002**: Cada plantilla de unidad MUST instanciarse a un archivo de gobierno que valida contra el
  contrato de la spec 002.
- **FR-003**: Cada plantilla de unidad MUST incluir su archivo de identidad, también la individual.
- **FR-004**: Las plantillas de artefacto de texto MUST NOT llevar campos de gobierno en su
  frontmatter, y su mapa de catálogo MUST ser texto a texto.
- **FR-005**: La plantilla de suite MUST cumplir los principios comprobables sobre el formato que el
  motor ejecuta: mínimo de casos, categoría declarada en todos, las tres categorías presentes y una
  aserción mecánica por caso.
- **FR-006**: La plantilla de hooks MUST declarar tope de tiempo por acción, apuntar dentro de la
  unidad y usar sólo eventos de la lista portable.
- **FR-007**: La instanciación MUST fallar si queda cualquier marcador sin sustituir.
- **FR-008**: El repositorio MUST tener pruebas automáticas de todo lo anterior, ejecutadas en CI en
  cada cambio que toque las plantillas o sus pruebas.

### Key Entities

- **Plantilla de unidad**: el envoltorio que toda unidad publicable lleva, con identidad y gobierno.
- **Plantilla de artefacto**: el punto de partida de un skill, un agente, un prompt, unos hooks, una
  configuración de servidor o una suite.
- **Marcador**: hueco a rellenar, con una forma reconocible a simple vista y por expresión regular,
  para que uno olvidado sea un error visible y no un valor plausible.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las plantillas del repositorio son byte a byte las del paquete de diseño.
- **SC-002**: Las tres comprobaciones de plantillas del `selfcheck.py` tienen prueba equivalente en la
  suite del repositorio.
- **SC-003**: Instanciar cualquier plantilla de unidad y validarla contra el contrato de gobierno pasa
  sin errores en el 100 % de los casos.
- **SC-004**: El asistente de autoría del hito 2 puede instanciar estas plantillas sin ajustarlas.

## Assumptions

- La prueba definitiva de esta spec, según el plan, es pasar las plantillas instanciadas por el
  validador de `std-003`, que todavía no existe. Hasta entonces se validan contra el contrato de
  gobierno de la spec 002, que es la parte que el validador delegará en el esquema de todos modos.
- Las plantillas se editan primero en el paquete de diseño, igual que los esquemas.
- Los comentarios de instrucciones dentro de las plantillas son parte del entregable: quien las copia
  los borra al rellenar.

## Clarifications

### Session 2026-09-07

- Q: ¿Contra qué se validan las plantillas si el validador de `std-003` no existe todavía? → A: contra
  el contrato de gobierno de la spec 002. Cuando exista el validador, la prueba se amplía en su spec.
- Q: ¿Se valida la plantilla de identidad de la unidad, si el estándar no publica un esquema para ese
  formato? → A: sí, pero con reglas propias y no con un esquema copiado: JSON válido, versión SemVer
  estricta y ningún campo fuera de los que el formato permite. Es lo que la revisión decidió para ese
  archivo.
- Q: ¿Entra la medición pendiente sobre dónde va el archivo de un skill dentro de una unidad
  individual? → A: no. Queda anotada en la plantilla; si la medición dice otra cosa, se ajusta la
  plantilla y el lineamiento, no el esquema.
