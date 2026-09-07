# Feature Specification: Prueba de humo de la organización

**Feature Branch**: `feat/001-smoke-org`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: ver `input.md` en esta carpeta (redactado a partir de la guía de
configuración de GitHub §10 y del plan global §3.7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Veredicto de la organización en una ejecución (Priority: P1)

Una persona del equipo de plataforma, antes de cerrar el hito 0 o antes de una demostración, lanza la
prueba de humo contra la organización y obtiene un veredicto global (pasa o no pasa) y un informe con
cada comprobación y, si falló, qué falta exactamente. No tiene que abrir ninguna pantalla de GitHub ni
comparar salidas a ojo.

**Why this priority**: es la razón de ser de la capacidad. Sin el veredicto, el resto no aporta nada.
Es el antídoto directo al error de la demo anterior: una propiedad exigida por el esquema que nadie
creó y nadie detectó.

**Independent Test**: se ejecuta contra la organización de demostración tal como está hoy y devuelve
verde; se retira a mano una variable de un marketplace, se vuelve a ejecutar y devuelve rojo señalando
esa variable en ese repositorio.

**Acceptance Scenarios**:

1. **Given** una organización configurada según la guía, **When** se ejecuta la prueba, **Then** todas
   las comprobaciones aparecen como superadas y el veredicto global es «pasa».
2. **Given** una organización a la que le falta un elemento exigido (un equipo, un secreto, una
   variable, un ruleset, el topic de un dominio), **When** se ejecuta la prueba, **Then** la
   comprobación correspondiente aparece como fallida con el nombre del elemento que falta y el
   repositorio o ámbito afectado, y el veredicto global es «no pasa».
3. **Given** una organización con varios fallos a la vez, **When** se ejecuta la prueba, **Then** el
   informe lista todos los fallos, no sólo el primero.
4. **Given** una ejecución que no puede consultar la organización (sesión sin autenticar, sin permiso
   o sin red), **When** se ejecuta la prueba, **Then** el resultado distingue «no se pudo comprobar» de
   «no pasa», dice qué faltó para poder comprobar y el veredicto no es «pasa».

---

### User Story 2 - Los tres requeridos del ruleset son exactos (Priority: P1)

La misma persona necesita la certeza de que el ruleset que protege la rama principal de cada
repositorio de dominio exige exactamente los tres contextos que el estándar fija, con el origen
correcto, porque un nombre distinto bloquea todas las solicitudes de cambio del dominio para siempre.

**Why this priority**: es el fallo más caro de la lista. Ya ocurrió dos veces en la demo anterior y
no hay manera de verlo desde un PR hasta que el PR queda bloqueado.

**Independent Test**: se ejecuta contra un repositorio de dominio cuyo ruleset tiene los tres
contextos exactos y pasa; se ejecuta contra uno con un contexto mal escrito, uno de menos o uno de más
y falla nombrando la diferencia.

**Acceptance Scenarios**:

1. **Given** un repositorio de dominio cuyo ruleset de rama principal exige exactamente los tres
   contextos del estándar, **When** se ejecuta la prueba, **Then** la comprobación pasa.
2. **Given** un ruleset con un contexto de menos, de más o con un nombre distinto por un carácter,
   **When** se ejecuta la prueba, **Then** la comprobación falla y el informe muestra los contextos
   esperados frente a los encontrados.
3. **Given** un repositorio de dominio sin ruleset de rama principal o sin el de etiquetas, **When**
   se ejecuta la prueba, **Then** la comprobación falla nombrando el ruleset ausente.

---

### User Story 3 - La misma prueba sirve para la demo y para BCP (Priority: P2, diferida)

**Diferida el 2026-09-07** al hito 8 (migración a BCP): entonces se conocerán los valores reales. En
esta spec sólo se garantiza la separación entre comprobaciones y valores esperados (FR-013), que es lo
que hace posible la historia después. No se entrega `bcp.json`.

Cuando el estándar se migre a la organización de BCP, la misma prueba de humo se ejecuta allí
cambiando sólo los valores esperados que difieren entre entornos (nombre de la organización, plan,
permiso base, nombres reales de los equipos), sin cambiar qué se comprueba.

**Why this priority**: la migración a BCP es el destino del proyecto, pero llega en el último hito.
Hasta entonces basta con que la separación entre comprobaciones y valores esperados exista.

**Independent Test**: se ejecuta con los valores esperados de la demo y pasa; se ejecuta con un
conjunto de valores esperados que declare otro plan y otro permiso base, contra la misma organización,
y fallan exactamente las comprobaciones de plan y permiso base.

**Acceptance Scenarios**:

1. **Given** dos conjuntos de valores esperados, uno para la demo y otro para BCP, **When** se
   ejecuta la prueba indicando cuál usar, **Then** las comprobaciones son las mismas y sólo cambian los
   valores contra los que se compara.
2. **Given** el mapa de papeles a equipos del estándar, **When** se ejecuta la prueba, **Then** los
   nombres de equipo que se exigen son los que declara ese mapa, no una lista aparte.

---

### Edge Cases

- Un repositorio de prueba temporal lleva el topic de dominio por error: la prueba lo señala como
  fallo, porque el generador del índice lo trataría como dominio.
- La App está instalada pero sólo en algunos repositorios: se señala como fallo, con los repositorios
  no cubiertos si la información está disponible.
- Un secreto existe pero con nombre distinto por mayúsculas o un guion: cuenta como ausente.
- El ruleset existe pero está desactivado o en modo evaluación: cuenta como fallo de ese ruleset.
- La organización tiene equipos o repositorios de más que la prueba no espera: no es fallo. La prueba
  comprueba lo que debe existir, no prohíbe lo demás, salvo el topic de dominio en repositorios que no
  son de dominio.
- La cuenta que ejecuta la prueba puede leer unos ámbitos y no otros: cada comprobación que no pudo
  consultarse se marca como «no comprobada», el veredicto global no puede ser «pasa» y el indicador de
  terminación es «no se pudo comprobar» aunque además haya fallos.
- La App está instalada con selección explícita de repositorios que incluye todos los esperados: pasa.
  Si la selección omite alguno de los esperados, falla nombrándolo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La prueba MUST comprobar que la organización existe y que su plan, su permiso base de
  miembros y su ajuste de creación de repositorios coinciden con los valores esperados del entorno.
- **FR-002**: La prueba MUST comprobar que existe cada equipo que declara el mapa de papeles a equipos
  del estándar (`config/teams.json`), tomando los nombres de ese mapa y no de una lista propia.
- **FR-003**: La prueba MUST comprobar que la App del ciclo de vida está instalada en la organización
  y que su instalación cubre todos los repositorios: bien porque declara cobertura de toda la
  organización, bien porque su selección explícita incluye todos los repositorios del entorno esperado.
  Cada repositorio esperado fuera de la instalación es un fallo que lo nombra.
- **FR-004**: La prueba MUST comprobar que cada repositorio de la plataforma y de dominio tiene los
  dos secretos de la App, por nombre exacto.
- **FR-005**: La prueba MUST comprobar que cada marketplace tiene las dos variables esperadas y que el
  valor del canal de cada marketplace es el que le corresponde.
- **FR-006**: La prueba MUST comprobar que todos los repositorios de dominio llevan el topic de
  descubrimiento y que ningún otro repositorio de la organización lo lleva.
- **FR-007**: La prueba MUST comprobar que cada repositorio de dominio tiene el ruleset de la rama
  principal (`protect-main`) y el ruleset de etiquetas (`protect-tags`), identificados por nombre
  exacto y ambos en modo activo. Un ruleset con otro nombre o en otro modo no cuenta.
- **FR-008**: La prueba MUST comprobar que el ruleset de la rama principal exige exactamente los tres
  contextos requeridos del estándar, sin otros, y que cada uno declara el origen esperado.
- **FR-009**: La prueba MUST ejecutar todas las comprobaciones aunque alguna falle, y el informe MUST
  listar todos los fallos.
- **FR-010**: Cada fallo del informe MUST nombrar el elemento que falta o difiere y el ámbito
  (organización, repositorio o equipo) al que pertenece; cuando hay un valor esperado y uno
  encontrado, MUST mostrar ambos.
- **FR-011**: La prueba MUST distinguir tres resultados por comprobación: superada, fallida y no
  comprobada (no se pudo consultar). El veredicto global MUST ser «pasa» sólo si todas están superadas.
- **FR-012**: La prueba MUST terminar con uno de tres indicadores que otro proceso pueda consumir sin
  leer el informe: pasa, no pasa, no se pudo comprobar. Si conviven comprobaciones fallidas y no
  comprobadas, el indicador es «no se pudo comprobar», porque el informe está incompleto. El informe
  legible para personas se emite en todos los casos.
- **FR-013**: Los valores esperados que difieren entre entornos (nombre de la organización, plan,
  permiso base, ajuste de creación de repositorios, lista de repositorios por tipo) MUST vivir
  separados de las comprobaciones, de modo que cambiar de entorno no cambie qué se comprueba.
- **FR-014**: Los nombres que son contrato del estándar (los tres contextos requeridos, los nombres de
  los dos secretos y de las dos variables, el topic de descubrimiento, el nombre de la App, los nombres
  de los dos rulesets) MUST estar definidos una sola vez y MUST ser los mismos que usan los workflows,
  los archivos de rulesets y la guía.
- **FR-015**: La prueba MUST ser de sólo lectura: no crea, modifica ni borra nada en GitHub.

### Key Entities

- **Entorno**: un conjunto de valores esperados para una organización concreta (demo o BCP): nombre,
  plan, permiso base, creación de repositorios, repositorios de plataforma, marketplaces con su canal y
  repositorios de dominio.
- **Comprobación**: una pregunta cerrada sobre la organización con un ámbito, un valor esperado, un
  valor encontrado y un resultado (superada, fallida, no comprobada).
- **Informe**: la lista de comprobaciones con su resultado y el veredicto global.
- **Mapa de papeles a equipos**: el archivo del estándar que dice qué equipo ejerce cada papel; es la
  fuente de los nombres de equipo esperados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona del equipo de plataforma obtiene el veredicto de la organización en una sola
  ejecución y en menos de un minuto, sin abrir ninguna pantalla de GitHub.
- **SC-002**: Cada uno de los diez elementos de la lista manual de la guía §10 tiene una comprobación
  equivalente; la lista manual deja de ser necesaria.
- **SC-003**: Al retirar a mano cualquier elemento exigido (un equipo, un secreto, una variable, un
  topic, un ruleset o un contexto), la siguiente ejecución lo señala con su nombre y su ámbito en el
  100 % de los casos probados.
- **SC-004**: La prueba pasa en verde contra la organización de demostración al cerrar el hito 0, y
  ese resultado es la evidencia de cierre del hito.
- **SC-005**: Cambiar de la demo a BCP requiere cambiar sólo valores esperados, cero comprobaciones.

## Assumptions

- Quien ejecuta la prueba tiene una sesión autenticada con permiso de lectura sobre la organización,
  sus equipos, sus instalaciones de Apps y los secretos y variables de los repositorios. Sin ese
  permiso la comprobación afectada queda «no comprobada», no «fallida».
- La prueba comprueba la estructura, no a las personas: no verifica quién es miembro de cada equipo ni
  si el autor de un PR podría aprobarlo. Eso es una decisión de reparto, no de configuración.
- La existencia de un secreto se comprueba por su nombre; su valor no es legible y no se valida.
- La lista de repositorios de dominio del entorno esperado es la fuente de verdad para «qué debe
  llevar el topic»; el topic en un repositorio fuera de esa lista es un fallo.
- Los ajustes de fusión y seguridad de cada repositorio (guía §5) y los permisos de los equipos sobre
  los repositorios (guía §6) quedan fuera de esta capacidad: la guía §10 no los incluye en la prueba
  de humo. Son candidatos a una spec posterior que amplíe la prueba.
- La prueba se ejecuta desde la máquina de una persona del equipo de plataforma. Ejecutarla de forma
  programada en la organización exigiría a la App permisos de administración que hoy no tiene y que la
  guía no pide; queda fuera de esta capacidad.

## Clarifications

### Session 2026-09-07

- Q: ¿La prueba verifica también los ajustes de fusión y seguridad por repositorio de la guía §5 (sólo
  squash, borrar rama al fusionar, sin wiki ni projects, secret scanning)? → A: No. Se limita a la
  lista de la guía §10. Los ajustes de §5 quedan para una spec posterior.
- Q: ¿La prueba verifica los permisos de los equipos sobre los repositorios (guía §6)? → A: No. Fuera
  de alcance en esta spec, para mantenerla pequeña; candidata a la misma spec posterior que §5.
- Q: ¿Cómo se distingue para otro proceso el veredicto «no pasa» del «no se pudo comprobar»? → A: Con
  tres indicadores de terminación distintos: pasa, no pasa, no se pudo comprobar. «No se pudo
  comprobar» prevalece sobre «no pasa» cuando conviven, porque el informe está incompleto.
- Q: ¿Cuándo se considera que la instalación de la App «cubre todos los repositorios»? → A: Cuando la
  instalación declara cobertura de todos los repositorios de la organización, o cuando su selección
  explícita incluye todos los repositorios del entorno esperado. Cualquier repositorio esperado fuera
  de la instalación es un fallo que lo nombra.
- Q: ¿Cómo se identifican los dos rulesets de un repositorio de dominio? → A: Por nombre exacto,
  `protect-main` y `protect-tags`, que pasan a ser nombres contrato del estándar, y por estar en
  modo activo. Un ruleset con otro nombre no cuenta aunque tenga las mismas reglas.
