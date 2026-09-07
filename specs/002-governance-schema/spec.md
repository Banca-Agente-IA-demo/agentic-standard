# Feature Specification: Esquemas de gobierno y de marketplace

**Feature Branch**: `feat/002-governance-schema`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `std-001-governance-schema` del PLAN-GLOBAL §5, hito 1. Spec Kit numera de forma
secuencial y `001` fue la prueba de humo del hito 0, así que la carpeta va desfasada un número
respecto al nombre del plan.

**Input**: `REVISION-ESQUEMAS-HITO-1.md` (decisiones D1 a D6, contrato) y el paquete de diseño
`hito-1-esquemas-y-plantillas/`, cuyo `selfcheck.py` está en verde y es el germen de las pruebas.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El estándar publica el contrato de `GOVERNANCE.json` (Priority: P1)

El equipo de plataforma necesita que exista, en un único sitio del repositorio del estándar, el
contrato del archivo `GOVERNANCE.json` que toda unidad publicable lleva en su raíz. Los nueve campos
que la revisión decidió, ni uno más. Todo lo que la demo anterior guardaba ahí y que hoy se deriva de
un hecho (estado, versión, dominio, inventario, aprobación, sello) queda rechazado por el propio
contrato, no por la buena voluntad de quien escribe.

**Why this priority**: el asistente de autoría, el validador, las plantillas y la ficha de Port
dependen de este contrato. Sin él no hay hito 1.

**Independent Test**: validar contra el esquema una unidad de ejemplo completa y otra mínima: las dos
pasan. Añadir a cualquiera de ellas un campo retirado de la demo: falla nombrando el campo.

**Acceptance Scenarios**:

1. **Given** un `GOVERNANCE.json` con los nueve campos bien formados, **When** se valida contra el
   esquema, **Then** no hay errores.
2. **Given** un `GOVERNANCE.json` sin uno de los cinco campos obligatorios, **When** se valida,
   **Then** falla indicando cuál falta.
3. **Given** un `GOVERNANCE.json` que reintroduce un campo retirado de la demo (`domain`, `status`,
   `version`, `standard_version`, `artifacts`, `certification`, `distribution`, `registry`,
   `$schema`), **When** se valida, **Then** falla por propiedad no permitida.
4. **Given** un `id` con la forma antigua de puntos, **When** se valida, **Then** falla.

---

### User Story 2 - El contrato hace cumplir las decisiones de gobierno que no se pueden vigilar a mano (Priority: P1)

Las decisiones D2, D4 y D6 sólo sirven si el archivo las impone. Una unidad no puede declarar dos
servidores MCP, unas credenciales sin custodio, un digest sin su prefijo, un comodín en los permisos
ni una obsolescencia a medias.

**Why this priority**: son las reglas que la revisión señaló como fuente de incidentes: una aprobación
de Ciberseguridad cubre un contrato, no dos; una credencial sin custodio deja al consumidor pidiendo
acceso a ciegas.

**Independent Test**: por cada regla, un caso que debe pasar y uno que debe fallar por esa razón
concreta.

**Acceptance Scenarios**:

1. **Given** un bloque `mcp` con dos servidores, **When** se valida, **Then** falla por exceso de
   propiedades.
2. **Given** `credentials` no vacía y sin `credentials_owner`, **When** se valida, **Then** falla
   nombrando `credentials_owner`; con `credentials` vacía, el custodio no hace falta y pasa.
3. **Given** un `tools_digest` sin el prefijo `sha256:`, **When** se valida, **Then** falla.
4. **Given** un `permissions.tools` con un comodín, **When** se valida, **Then** falla.
5. **Given** un bloque `deprecation` al que le falta cualquiera de sus tres campos, o con una fecha
   que no es ISO, **When** se valida, **Then** falla.
6. **Given** un `superseded_by` con el valor literal `none`, **When** se valida, **Then** pasa,
   porque «sin sucesor» es una decisión explícita (D6).

---

### User Story 3 - El índice del marketplace se valida por proyección de cliente (Priority: P1)

El archivo que genera el workflow del marketplace tiene dos proyecciones, una por cliente, que se
diferencian sólo en cómo direccionan una unidad que vive en un subdirectorio. La divergencia está
medida: Copilot rechaza `git-subdir` y Claude Code acepta `github` con `path` pero lo ignora e instala
el repositorio entero sin dar error. El contrato tiene que impedir las dos combinaciones equivocadas,
y admitir versiones con sufijo de prelanzamiento, que es lo que lista el canal experimental.

**Why this priority**: un índice mal formado no falla de forma visible, instala otra cosa. Y un índice
vacío desinstala de golpe todo lo que ofrecía.

**Independent Test**: validar cada uno de los dos índices de ejemplo contra su propia proyección
(pasan) y contra la ajena (fallan).

**Acceptance Scenarios**:

1. **Given** el índice con fuentes `git-subdir`, **When** se valida contra la proyección de Claude
   Code, **Then** pasa; contra la de Copilot, falla.
2. **Given** el índice con fuentes `github` más `path`, **When** se valida contra la proyección de
   Copilot, **Then** pasa; contra la de Claude Code, falla.
3. **Given** una versión de unidad con sufijo de prelanzamiento, **When** se valida, **Then** pasa;
   con metadatos de compilación, falla.
4. **Given** una lista de unidades vacía, **When** se valida, **Then** falla.
5. **Given** cualquier índice validado contra la raíz del esquema en vez de contra una proyección,
   **When** se valida, **Then** falla, para que un validador mal apuntado no pase en vacío.

---

### Edge Cases

- `x_extensions` admite cualquier contenido y no se valida: es la válvula de escape declarada.
- Un `schema_version` que el estándar no conoce se rechaza por el enumerado.
- La versión del propio índice no admite sufijo, aunque las de las unidades sí.
- Un `owner.contact` que no es un correo, o un `access_request_url` que no es una URL, fallan por
  formato.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El repositorio MUST publicar `schemas/governance.schema.json` y
  `schemas/marketplace.schema.json`, copiados sin modificación del paquete de diseño del hito 1.
- **FR-002**: `governance.schema.json` MUST aceptar exactamente los nueve campos decididos y rechazar
  cualquier otro de primer nivel.
- **FR-003**: `governance.schema.json` MUST exigir `schema_version`, `id`, `owner`,
  `data_classification` y `permissions`, y dejar opcionales los cuatro restantes.
- **FR-004**: El esquema MUST imponer las cotas de D2: como mucho un servidor en el bloque `mcp` y en
  `permissions.mcp_servers`, custodio obligatorio cuando hay credenciales, y digest con prefijo.
- **FR-005**: El esquema MUST imponer D6: los tres campos de `deprecation` cuando el bloque existe, y
  `none` como valor admitido de `superseded_by`.
- **FR-006**: `marketplace.schema.json` MUST validarse por proyección de cliente y su raíz MUST
  rechazar cualquier documento.
- **FR-007**: Las versiones de las unidades del índice MUST admitir sufijo de prelanzamiento y
  rechazar metadatos de compilación; la versión del índice MUST rechazar el sufijo.
- **FR-008**: El repositorio MUST tener pruebas automáticas que cubran cada escenario de aceptación,
  con un nombre que diga el defecto que cubre, y MUST ejecutarlas en CI en cada cambio que toque los
  esquemas o sus pruebas.
- **FR-009**: El repositorio MUST NOT publicar esquemas de formatos de cliente (skill, agente,
  prompt, hooks, `.mcp.json`, `plugin.json`) ni de suite de evals.

### Key Entities

- **Contrato de gobierno**: el esquema de `GOVERNANCE.json`, con sus nueve campos.
- **Contrato del índice**: el esquema del archivo generado, con dos proyecciones.
- **Unidad de ejemplo**: una instancia real de `GOVERNANCE.json`, completa o mínima, que sirve de
  prueba y de documentación viva del contrato.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los dos esquemas del repositorio son byte a byte los del paquete de diseño, cuya
  autocomprobación está en verde.
- **SC-002**: Cada comprobación de `check_governance` y `check_marketplace` del `selfcheck.py` tiene
  una prueba equivalente en la suite del repositorio.
- **SC-003**: Reintroducir cualquiera de los nueve campos retirados de la demo falla en el 100 % de
  los casos probados.
- **SC-004**: `std-002` y `std-003` pueden partir de estos esquemas sin tocar su contenido.

## Assumptions

- Los esquemas se validan con JSON Schema 2020-12 y comprobación de formatos activada, igual que la
  autocomprobación del paquete de diseño.
- Las instancias de ejemplo viven como material de prueba del repositorio. Su valor documental es un
  efecto secundario deseable, no su función.
- Las reglas que el esquema no puede expresar (que la primera mitad del `id` sea el repositorio real,
  que el nombre del servidor coincida con `.mcp.json`, que el equipo exista en la organización) son de
  `std-003` y no de esta spec.
- El esquema todavía no viaja como dato dentro de un paquete instalable: eso llega con el validador de
  `std-003`. Aquí vive en `schemas/` y las pruebas lo leen por ruta.

## Clarifications

### Session 2026-09-07

- Q: ¿Dónde viven las instancias de ejemplo del paquete de diseño? → A: en el material de prueba del
  repositorio, junto a las pruebas que las consumen, no en una carpeta de ejemplos aparte. Su función
  aquí es ser fixtures.
- Q: ¿Se copian también las plantillas en esta spec? → A: no. Las plantillas son `std-002`; esta spec
  se limita a los dos esquemas y sus pruebas.
- Q: ¿Qué pasa con las dependencias que las pruebas necesitan? → A: la validación de JSON Schema entra
  como dependencia de desarrollo del repositorio. La dependencia de ejecución la declarará el paquete
  del validador en `std-003`.
