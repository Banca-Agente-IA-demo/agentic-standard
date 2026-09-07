# Asistente de autoría

Acompaña a quien crea, modifica o deprecia una unidad publicable. Pregunta lo que hace falta, deja que
los scripts decidan, y prepara la solicitud de cambio.

Es un plugin del estándar y **se gobierna con las mismas reglas que publica**: lleva su identidad, su
gobierno y sus pruebas, y pasa por el mismo validador que cualquier unidad de un dominio.

## Cómo está hecho

| Pieza | Qué es |
|---|---|
| `skills/author-unit/SKILL.md` | El punto de entrada. Corto: lo largo vive en `references/` y se carga sólo cuando hace falta |
| `skills/author-unit/scripts/` | Los puntos de entrada de cada script: parsean argumentos, cablean adaptadores e imprimen un JSON |
| `authoring_assistant/` | El núcleo, por capas. `domain` puro, `application` orquesta, `ports` sólo donde hay más de una implementación, `adapters` habla con el exterior |
| `validator.lock` | La etiqueta y el commit del estándar cuyo validador se instala en el entorno privado del plugin |
| `tests/` | Viajan con la unidad, como exige el estándar. Son inofensivas para quien la instala |

## Los dos principios que ordenan el resto

**Los scripts deciden; el modelo pregunta, presenta y lee un campo del JSON.** Nunca se interpreta la
salida de git ni el contenido de un archivo para decidir. Un diálogo que interpreta a ojo se equivoca
distinto cada vez y no se puede probar; un script se prueba una vez y se equivoca siempre igual.

**No se toca trabajo ajeno.** El asistente sólo actúa sobre la rama de trabajo actual. Nunca descarta
cambios sin confirmar, nunca reescribe el historial y nunca hace nada sobre otra rama. Un estado de
git que no sepa manejar detiene el asistente con el mensaje de qué corregir.

## Qué necesita la máquina del autor

Python 3.11 o superior con `pip` y `venv`, `git`, y `gh` con una sesión activa. **No se instala nada a
mano**: los clientes clonan la carpeta del plugin y los scripts añaden su raíz al camino de importación.
El paquete usa sólo la biblioteca estándar. La única instalación que ocurre alguna vez es la del
validador del estándar, que el asistente hace en un entorno privado la primera vez que se usa, a la
versión que fija `validator.lock`.

## Estado

Esqueleto del hito A0. El plugin se instala y se lista, pero todavía no hace nada: el núcleo
determinístico es el hito A1 y el diálogo el A2. Falta su suite de evaluación, y el validador lo avisa
con razón: llegará cuando el skill tenga contenido que evaluar.
