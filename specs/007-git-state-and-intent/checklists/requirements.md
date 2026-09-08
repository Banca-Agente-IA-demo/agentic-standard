# Checklist de requisitos: El asistente sabe dónde está antes de proponer nada

Se pasa sobre [spec.md](../spec.md) antes de dar la capacidad por cerrada.

## Lo que la spec tenía que fijar

- [x] CHK001 Los seis estados llevan los nombres del árbol de decisión, sin inventar ninguno (FR-001)
- [x] CHK002 Cada estado dice qué necesita el diálogo a continuación (FR-002)
- [x] CHK003 Cada estado de parada lleva qué corregir y con qué comando (FR-003)
- [x] CHK004 La forma del nombre de rama es la de las reglas de rama y versión (FR-004)
- [x] CHK005 Los dos avisos de atraso están cubiertos, el de la rama principal y el de la de trabajo
      (FR-005)
- [x] CHK006 Un manifiesto ilegible consta en la salida en vez de desaparecer (FR-006)
- [x] CHK007 La intención sobrevive a cerrar la sesión y no viaja al clonar (FR-007)
- [x] CHK008 Leer, guardar y borrar devuelven la misma forma de documento (FR-008)
- [x] CHK009 Una acción guardada que no es válida no se da por buena (FR-009)
- [x] CHK010 La comprobación cubre el intérprete con su versión mínima, git y la herramienta de
      GitHub (FR-010)
- [x] CHK011 Un documento en la salida estándar y el diagnóstico en la de error (FR-011)
- [x] CHK012 Éxito en toda clasificación, fallo sólo cuando no se pudo ejecutar (FR-012)
- [x] CHK013 Las reglas se prueban con datos, sin repositorio y sin red (FR-013)
- [x] CHK014 Los scripts funcionan sin instalar nada, sólo con la biblioteca estándar (FR-014)

## Lo que no se decidió a la ligera

- [x] CHK015 Toda decisión que el diseño no fijaba está en las clarificaciones de la spec, con su
      motivo, y no escondida en el código
- [x] CHK016 Los dos defectos medidos al portar los prototipos, el código de salida y la salida
      mezclada, tienen su prueba de regresión (T3)
- [x] CHK017 El hallazgo de que el directorio personal de esta máquina es un repositorio quedó
      escrito donde lo vea quien toque esa prueba

## Lo que quedó fuera a propósito

- [x] CHK018 El asistente no ejecuta ningún comando de git que escriba: esta capacidad sólo mira
- [x] CHK019 La redacción del diálogo no está aquí, llega con la capacidad del skill
- [x] CHK020 `ports/` sigue vacío: ninguno de los tres adaptadores tiene una segunda implementación
