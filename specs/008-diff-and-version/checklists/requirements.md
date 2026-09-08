# Checklist de requisitos: Clasificación del diff y salto de versión

Se pasa sobre [spec.md](../spec.md) antes de dar la capacidad por cerrada.

## Lo que la spec tenía que fijar

- [x] CHK001 El diff va acotado a la carpeta de la unidad y se compara contra la rama principal
      (FR-001)
- [x] CHK002 Cada fila de la tabla tiene su prueba y cada motivo nombra la ruta (FR-002)
- [x] CHK003 Cuando el cambio cae en varias filas manda la más alta y constan todos los motivos
      (FR-003)
- [x] CHK004 Un cambio vacío se dice y no propone salto (FR-004)
- [x] CHK005 Retirar un artefacto es el salto que corresponde a romper a quien la consume (FR-005)
- [x] CHK006 Un movimiento cuenta como retirada más alta, no como cambio de texto (FR-005)
- [x] CHK007 Borrar un archivo que no es artefacto no eleva por sí solo (FR-006)
- [x] CHK008 La propuesta es estrictamente mayor que la publicada, con precedencia de prelanzamientos
      (FR-007)
- [x] CHK009 La última publicada sale de los lanzamientos que no son borrador (FR-008)
- [x] CHK010 Sin nada publicado, la propuesta es la versión inicial y no hay menú (FR-009)
- [x] CHK011 Toda propuesta lleva sufijo, y el contador sube o se reinicia según el nivel (FR-010)
- [x] CHK012 Un nivel por debajo del mínimo se rechaza (FR-011)
- [x] CHK013 Sin la orden de aplicar no se escribe nada (FR-012)
- [x] CHK014 Al aplicar se escribe sólo el manifiesto, y el destino se comprueba antes (FR-013)
- [x] CHK015 Las dos entradas consumen un solo caso de uso (FR-014)
- [x] CHK016 Las reglas se prueban con datos, y la suite entera sin red (FR-015, FR-016)

## Lo que no se decidió a la ligera

- [x] CHK017 La fila que la tabla no tenía está marcada como decisión de esta spec, con su motivo, y
      señalada como pendiente de confirmar
- [x] CHK018 Los lanzamientos de otra unidad del mismo repositorio no cuentan para esta
- [x] CHK019 Los defectos medidos al escribir las pruebas tienen su comentario de dónde se midieron

## Lo que quedó fuera a propósito

- [x] CHK020 Promocionar una versión, que es retirar el sufijo, es otro camino
- [x] CHK021 Descartar un prelanzamiento no es una versión nueva y no vive aquí
- [x] CHK022 La redacción del menú y la elección del nivel son del diálogo
- [x] CHK023 `ports/` sigue con un solo puerto
