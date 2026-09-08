# Checklist de requisitos: Estado de la unidad en su ciclo de vida

Se pasa sobre [spec.md](../spec.md) antes de dar la capacidad por cerrada.

## Lo que la spec tenía que fijar

- [x] CHK001 El estado se deriva y no se declara en ningún archivo (FR-001)
- [x] CHK002 Los estados derivables llevan los valores técnicos del lineamiento (FR-002)
- [x] CHK003 Sin nada publicado ni en borrador, el mensaje es el del nodo de parada (FR-003)
- [x] CHK004 Sólo con prelanzamientos, la unidad es experimental (FR-004)
- [x] CHK005 Con una final, la unidad está en producción aunque haya una beta por delante, y esa beta
      consta (FR-005)
- [x] CHK006 Sin publicados y con borradores, el estado no se afirma y se avisa (FR-006)
- [x] CHK007 Sólo se ofrece obsoletar lo que está en experimental o en producción (FR-007)
- [x] CHK008 La consulta devuelve la última publicada y si hay alguna final (FR-008)
- [x] CHK009 Los lanzamientos de otra unidad no cuentan para ésta (FR-009)
- [x] CHK010 Todo se prueba con datos y sin red (FR-010)
- [x] CHK011 La consulta no lee ni escribe nada del repositorio del autor (FR-011)

## Lo que no se decidió a la ligera

- [x] CHK012 El resultado que no afirma el estado no lleva ninguno de los seis nombres del ciclo de
      vida, que son contrato persistido en el catálogo
- [x] CHK013 La razón de no poder distinguir suspendida de retirada está escrita, no supuesta

## Lo que quedó fuera a propósito

- [x] CHK014 Descartar un prelanzamiento sigue siendo un hueco del documento y no se resuelve aquí
- [x] CHK015 Quién sustituye a una unidad obsoleta se lee del índice del marketplace y llega con el
      camino de la obsolescencia
- [x] CHK016 `ports/` sigue con un solo puerto, ahora con dos consumidores
