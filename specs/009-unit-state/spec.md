# Feature Specification: Estado de la unidad en su ciclo de vida

**Feature Branch**: `feat/009-unit-state`

**Created**: 2026-09-07

**Status**: Draft

**Corresponde a**: `003-unit-state` del hito A1 del plan del asistente. Aquí es la spec 009 porque la
numeración de este repositorio es secuencial.

**Input**: el nodo G0b del árbol de decisión con su fila de la tabla, el §6 del lineamiento del ciclo
de vida con la máquina de estados, y `PLAN-DE-TRABAJO-ASISTENTE-AUTORIA` §1.4 para el contrato de
salida.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No se ofrece obsoletar lo que nunca se publicó (Priority: P1)

Quien pide obsoletar una unidad que todavía no ha salido recibe que no hay nada que obsoletar, en vez
de un camino que acabaría en un cambio sin efecto.

**Por qué es P1**: es el nodo de parada del camino de la obsolescencia. Sin él, el asistente lleva al
autor por cinco pasos para acabar publicando un aviso sobre algo que nadie ha instalado.

**Prueba independiente**: se clasifica una unidad sin lanzamientos y se comprueba el estado y el
mensaje.

**Escenarios de aceptación**:

1. **Dado** que la unidad no tiene ningún lanzamiento, **cuando** se consulta su estado, **entonces**
   está en desarrollo y el asistente dice que no hay nada que obsoletar.
2. **Dado** que la unidad sólo tiene prelanzamientos, **cuando** se consulta, **entonces** está en
   experimental y sí se puede obsoletar.
3. **Dado** que la unidad tiene una versión final, **cuando** se consulta, **entonces** está en
   producción y sí se puede obsoletar.

### User Story 2 - Una unidad retirada no se anuncia como si estuviera empezando (Priority: P1)

Quien consulta una unidad suspendida o retirada no recibe que está en desarrollo.

**Por qué es P1**: suspender y retirar ponen los lanzamientos en borrador, así que esas unidades tienen
cero lanzamientos publicados y se leerían como si nunca hubieran salido. Decirle a quien tiene una
unidad suspendida que está en desarrollo es decirle algo falso sobre algo que sus consumidores ya
tenían instalado.

**Prueba independiente**: se clasifica una unidad cuyos lanzamientos son todos borradores.

**Escenarios de aceptación**:

1. **Dado** que la unidad no tiene lanzamientos publicados pero sí borradores, **cuando** se consulta,
   **entonces** el asistente no afirma que esté en desarrollo y avisa de que puede estar suspendida o
   retirada.
2. **Dado** ese mismo caso, **cuando** se consulta, **entonces** tampoco se ofrece obsoletarla.

### User Story 3 - Una versión nueva no saca a la unidad de producción (Priority: P2)

Quien tiene una versión en prueba por delante de la que está en producción ve las dos cosas: que la
unidad sigue en producción y que hay una versión en vuelo.

**Por qué es P2**: la transición de canal es de la unidad, no de la versión publicada. Confundirlas
haría que publicar una prueba pareciera una retirada de producción.

**Escenarios de aceptación**:

1. **Dado** que la última publicada es un prelanzamiento y existe una versión final anterior,
   **cuando** se consulta, **entonces** la unidad está en producción y consta que hay una versión en
   vuelo.

### Edge Cases

- Una etiqueta que no es una versión se descarta sin romper la consulta.
- Los lanzamientos de otra unidad del mismo repositorio no dicen nada de ésta.
- Un borrador no cuenta como publicado cuando hay publicados.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El estado MUST derivarse de los lanzamientos y MUST NOT declararse en ningún archivo.
- **FR-002**: Los estados derivables MUST llevar los valores técnicos del lineamiento del ciclo de
  vida.
- **FR-003**: Sin ningún lanzamiento publicado ni borrador, la unidad MUST estar en desarrollo y el
  mensaje MUST ser el del nodo de parada.
- **FR-004**: Con lanzamientos publicados y todos en prelanzamiento, la unidad MUST estar en
  experimental.
- **FR-005**: Con al menos una versión final publicada, la unidad MUST estar en producción, aunque
  haya un prelanzamiento por delante, y ese prelanzamiento en vuelo MUST constar.
- **FR-006**: Sin lanzamientos publicados pero con borradores, el estado MUST NOT afirmarse y MUST
  avisarse de que la unidad puede estar suspendida o retirada.
- **FR-007**: Sólo MUST poder obsoletarse una unidad en experimental o en producción.
- **FR-008**: La consulta MUST devolver la última versión publicada y si existe alguna final.
- **FR-009**: Los lanzamientos de otra unidad del repositorio MUST NOT contar para ésta.
- **FR-010**: Las reglas MUST poder probarse con datos, sin red y sin lanzamientos de verdad.
- **FR-011**: La consulta MUST NOT leer ni escribir nada del repositorio del autor.

### Key Entities

- **Estado de la unidad**: el punto del ciclo de vida, la última publicada, si hay final, si hay un
  prelanzamiento en vuelo y si se puede obsoletar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada estado derivable tiene su prueba, y también el caso que no se afirma.
- **SC-002**: La suite corre sin red.
- **SC-003**: Consultar el estado no toca el repositorio del autor.

## Assumptions

- Distinguir una unidad suspendida de una retirada necesita la ficha del catálogo, que esta capacidad
  no lee. Por eso avisa en vez de afirmar.
- Descartar un prelanzamiento, que es poner su lanzamiento en borrador, sigue siendo un hueco del
  documento y queda fuera.
- Quién sustituye a una unidad obsoleta se lee del índice del marketplace, no de los lanzamientos, y
  llega con el camino de la obsolescencia.

## Clarifications

### Session 2026-09-07

- Q: ¿Qué pasa con una unidad suspendida o retirada, cuyos lanzamientos están en borrador? → A: no se
  afirma el estado. Es un resultado nuevo, `indeterminate`, que **no** es uno de los seis del ciclo de
  vida y por eso no lleva ninguno de sus nombres: dice lo que se sabe, que no hay nada publicado y sí
  borradores, y manda comprobarlo en el catálogo. Dejarlo como desarrollo era el comportamiento por
  omisión y era falso.
- Q: ¿Una unidad con una beta por delante de la final sigue en producción? → A: sí. La transición de
  canal es de la unidad, no de la versión publicada. Que haya una beta en vuelo es un dato aparte, y
  se expone como tal.
- Q: ¿Dónde vive esto? → A: en su propio caso de uso, no junto al de la versión. Derivar el estado del
  ciclo de vida y calcular un salto de versión son dos cosas, aunque las dos lean los lanzamientos.
