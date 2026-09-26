"""El paso de creación de una unidad: un solo step del workflow, cuatro bandas por dentro.

Por qué existe. El flujo anterior repartía la creación en cuatro composite actions, así que el orden
de las cosas solo se leía en el YAML. Aquí el orden está en `create_unit.py` y el YAML queda con un
step, que es lo que pide el diagrama de autoría.

La disposición es la de E2, igual que la de cualquier otro nodo del circuito:

| Banda | Qué hace |
|---|---|
| `input_sub_process` | Lee el formulario de Port y lo convierte en petición de dominio |
| `pre_sub_process` | Pregunta al catálogo: equipo, nombres ocupados y si el de esta unidad lo está |
| `orchestration_sub_process` | Siembra el esqueleto bajo la raíz de trabajo |
| `output_sub_process` | Compone el veredicto que sale del proceso |

NO DEFINE UNA JERARQUÍA DE ERRORES PROPIA, y no es un olvido. Este paso no tiene imposibilidades
propias: las dos que puede encontrar ya tienen base declarada, `CatalogError` del catálogo y
`SeedError` del sembrador, y el adaptador las captura por separado. Envolverlas en una tercera base
con un solo implementador sería indirección sin beneficio, que es lo que la sección 14 del estándar
descarta. Si algún día este paso tiene una imposibilidad suya, aquí es donde va su base.

Trazabilidad. `CONVERGENCIA-CREATE-UNIT.md`. AGENTS.md E2, E5, X1 y sección 14.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
