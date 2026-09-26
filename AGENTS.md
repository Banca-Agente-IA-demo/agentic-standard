# Estándar de código

Este documento es la referencia de código del proyecto y la norma a seguir a partir de ahora.

De dónde sale. La columna vertebral son las prácticas extraídas del código real de
`ejemplo_codigo/last_version` (un circuito de migración de Atlas a CNF, 391 módulos Python y 213
pasos), recogidas en `PRACTICAS-CODIGO-EJEMPLO.md`. No son una propuesta: describen algo que ese
código ya hace de forma consistente, y cuando el propio código explica por qué lo hace, ese porqué
está aquí. Sobre esa base se añaden dos bloques que ese código no cubre: **logging**, del que no
tiene ni una línea en sus 391 módulos, y **workflows de GitHub Actions**, de los que no dice nada.

Cómo leerlo si acabas de llegar. Las secciones van de lo grande a lo pequeño: dónde va cada archivo,
qué promete cada pieza, cómo se escribe una función, y qué se comprueba antes de empujar. Cada regla
tiene un código estable, dice qué exige y por qué (con el defecto concreto que previene cuando se
conoce), y lleva ejemplo cuando el ejemplo aporta algo. Al final hay una checklist de revisión y una
sección corta sobre lo que este estándar deliberadamente no adopta, para que nadie lo introduzca
creyendo que corrige un descuido.

Las reglas marcadas **(ya se cumple)** describen algo que el código de ejemplo ya hace. Están
escritas porque una costumbre no escrita se pierde con la primera persona que se incorpora.

---

## 1. Estructura

### E1 · Disposición `src`, y nada importable por accidente

El paquete vive bajo `src/` y solo se instala lo declarado. El motivo que da el propio
`pyproject.toml` del ejemplo es literal: «para que nada sea importable por accidente desde la raíz
del repositorio».

El **adaptador de la línea de órdenes vive fuera del paquete** (`scripts/transform.py`), y es
deliberado: traduce argumentos a una llamada y no forma parte de la superficie importable.

### E2 · Un proceso es cuatro bandas, siempre las mismas

Cada nodo del circuito (`analyze`, `plan`, `migrate`, `validate`, `judge`) tiene exactamente la
misma anatomía:

```
<nodo>/
├── <nodo>.py                    ← encadena las cuatro bandas. No decide nada
├── contract.py                  ← qué promete el nodo, declarativo
├── commons/
│   ├── enums/
│   └── models/
│       ├── seams.py             ← los sellos internos del nodo
│       └── evidence_blocks.py
├── input_sub_process/
│   ├── input_sub_process.py     ← encadena sus pasos
│   └── steps/                   ← un archivo por paso
├── pre_sub_process/
├── orchestration_sub_process/
└── output_sub_process/
```

La repetición es el punto: quien conoce un nodo conoce los cinco. Buscar «dónde se valida la
entrada» no requiere leer nada, se deduce de la ruta.

La organización es **por proceso y banda**, no por capas técnicas. La sección final explica por qué.

### E3 · El archivo que compone no calcula

Un `<nodo>.py` y un `<banda>_sub_process.py` solo dicen **en qué orden** se llama a qué y **qué
necesita cada uno**. El código de ejemplo lo escribe en el docstring sin rodeos: «Aquí no se decide
nada» y «Aquí no se calcula nada: cada paso es una función de `steps/`».

Si un compositor tiene un `if` sobre el contenido de algo, ese `if` pertenece a un paso.

### E4 · Un archivo por paso, y una sola función exportada

Cada paso es su propio archivo en `steps/`, con un `__all__` de un solo nombre. No se agrupan tres
pasos afines en un módulo «de utilidades». Las funciones privadas que el paso necesite viven en el
mismo archivo, con prefijo `_` (ver P8).

### E5 · `commons/` por nodo y `commons/` global

Lo compartido dentro de un nodo vive en su `commons/`; lo compartido entre nodos, en el `commons/`
del paquete. Un modelo que dos nodos leen **sube**; uno que solo usa un nodo **no baja** de más.

### E6 · Una sola responsabilidad por unidad, y el tamaño como aviso *(ya se cumple)*

Cada función, módulo o job hace **una sola cosa**. Si para describir lo que hace hace falta la
conjunción «y», divídelo. La regla aplica al **archivo entero**, no solo a sus funciones: un módulo
donde cada función está bien pero que en conjunto parsea, juzga, persiste y reporta sigue
incumpliendo.

Dos chequeos explícitos, porque el juicio a ojo falla:

- **Test de la conjunción:** si describir el archivo necesita «y», cada cláusula es un módulo
  candidato.
- **Test de grupos:** si sus funciones caen en más de un grupo temático (parseo, juez, persistencia,
  reporte, orquestación), cada grupo es candidato a su propio módulo.

**Disparador por tamaño (aviso, no límite duro).** Un módulo Python que supera ~300 líneas es una
*señal* de que probablemente acumula más de una responsabilidad. Al cruzar el umbral es obligatorio
o dividirlo, o dejar un comentario al inicio justificando por qué la cohesión real lo amerita. Nunca
se cruza el umbral en silencio. El tamaño es un proxy: la regla real es la cohesión, y dividir por
el número, rompiendo una unidad genuina, es peor que no dividir.

La disposición E2/E4 ya empuja hacia aquí: un archivo por paso con una función exportada es
responsabilidad única por construcción.

---

## 2. Contratos y fronteras

### C1 · Cada nodo declara su contrato en un archivo, aparte del código que lo cumple

`contract.py` enumera qué produce el nodo, con qué claves, qué señales emite y quién las consume. Es
declaración, no ejecución: se puede cruzar entre nodos **sin correr nada**.

El contrato existe porque esa información estaba escrita **tres veces y en tres sitios distintos**
(el prompt del comando, la sección de salidas de la invocación y los `test -f` del YAML) y nada
garantizaba que dijeran lo mismo. De hecho no lo decían.

### C2 · Pydantic en la frontera exterior, `dataclass(frozen=True)` dentro

| | Qué se usa | Por qué |
|---|---|---|
| Lo que **entra desde fuera** (un JSON que escribió otro proceso) | modelo **pydantic** | es el punto exacto donde los datos entran al sistema de tipos desde fuera; `model_validate()` falla en el sitio y con el nombre del campo, no tres funciones más tarde |
| Lo que **viaja entre bandas** de un mismo nodo | `@dataclass(frozen=True)` | no sale del proceso, no se serializa; lo que se le pide es estructura e inmutabilidad, «que una banda no reescriba lo que otra cerró» |

Añade `slots=True` a las dataclasses de declaración. No es optimización, es una comprobación: sin
slots, `spec.labls = (...)` (con la errata) crearía un atributo nuevo sin protestar y el valor real
quedaría vacío; con slots, revienta al escribirlo.

Un contrato se escribe como **instancia constante de módulo**, no como clase por nodo:
`ANALYZE_CONTRACT = NodeContract(...)`. Una clase con una sola instancia invita a meterle
comportamiento dentro de algo que tiene que seguir siendo una declaración.

Decir «usa `@dataclass`» y parar ahí no basta: no dice dónde acaba la validación y empieza la
estructura, que es justo la línea que esta regla traza.

### C3 · Si ya se parseó, no se vuelve a parsear: se transporta

Nace de un defecto real: el mismo archivo se parseaba tres veces en tres funciones con tres
criterios, y dos de ellas divergieron sin que nadie lo notara. El único parseo obligatorio es el del
productor, que tiene que abrir el archivo de todos modos; ese parseo construye el modelo y **el
modelo viaja**.

### C4 · Una convención se escribe una vez

Las rutas del circuito se derivan en un solo módulo. Antes había cuatro funciones derivando la misma
convención, «y ninguna sabía de las otras», conviviendo con cinco salidas que el emisor emitía y
nadie leía: «funcionaba por coincidencia».

Es la regla de no duplicar, sin atenuantes: si la misma lógica aparece en dos lugares, se extrae.
No hay excepción por «es solo una línea» ni por «son archivos distintos».

### C5 · Lo que se declara y lo que se implementa se cruzan automáticamente

Hay un comprobador (`check_contracts`) que verifica que el grafo de contratos cierre: que la clave
que un nodo declara producir sea la que otro declara leer, y que el modelo diga lo mismo que el
contrato. **Sin ejecutar el circuito.**

### C6 · Una clave entra al contrato solo si alguien declara leerla

Un contrato no es el esquema completo de un archivo: es la intersección de lo que se promete con lo
que alguien consume. Por eso el campo `source` de cada clave es obligatorio: dice quién la lee, y
sin ese dato la clave no tiene justificación para estar declarada.

### C7 · El verificador no repara

Cuando la banda de salida encuentra un incumplimiento, no lo corrige: lo nombra y enruta. Un
verificador que repara enmascara el defecto del productor y deja de ser comparable consigo mismo
entre ejecuciones. Si sobra un temporal en la salida, la corrección va en la capacidad que lo creó.

### C8 · Todo dato estructurado tiene tipo propio

Ninguna firma declara `dict`, `Mapping`, `object`, `Any` ni sus combinaciones (`dict[str, Any]`,
`list[dict]`) para datos del dominio. Si el dato tiene campos, tiene un tipo, y ese tipo vive en
`commons/models/` del nivel que le toca (E5). Lo mismo para los valores: un conjunto cerrado es un
enumerado (T1) y un número que gobierna comportamiento es una constante nombrada (T6). **Un dato sin
tipo propio es un dato que nadie declara.**

**La única ventana**, y es de una línea: el valor que devuelve `json.loads` antes de pasarlo a
`model_validate()`. Ese instante es la frontera, y C2 dice qué hay a cada lado. A partir de ahí
viaja el modelo, que es C3.

**El defecto que previene.** Un `dict` no falla cuando falta una clave ni cuando el nombre llega con
una errata: devuelve `None`, o revienta tres funciones más tarde y en otro archivo, con un
`KeyError` que no dice quién tenía que haberla puesto. Es el mismo argumento que `slots=True` en C2,
aplicado a la estructura entera en vez de a un campo.

Y hay una razón de contrato, no solo de comodidad: **`check_contracts` cruza lo declarado con lo
implementado sin ejecutar nada** (C5). Un `dict[str, Any]` no declara nada, así que un nodo que lo
use queda fuera de esa comprobación sin que el comprobador pueda avisar.

```python
# MAL · la forma del dato solo existe en la cabeza de quien lo escribio
def compose_finding(data: dict) -> dict:
    return {"owner": data["owner"], "detail": data.get("detail", "")}

# BIEN · la forma esta declarada, y `check_contracts` la puede leer
@dataclass(frozen=True, slots=True)
class Finding:
    owner: Owner            # enumerado, no cadena (T1)
    detail: str

def compose_finding(request: FindingRequest) -> Finding: ...
```

**Qué hacer cuando el dato de fuera no tiene forma fija**, como el payload de un proceso ajeno cuyas
claves cambian según quién lo emita: se declaran las variantes que se leen, una por emisor, y se
elige con un enumerado. La regla no admite `Mapping[str, object]` como atajo, y el motivo es que ese
atajo **esconde precisamente la diferencia que hay que declarar**: si tres emisores mandan tres
formas, el código que las trata por igual funciona hasta que una cambia.

**Es verificable, y debe verificarse** con una prueba estructural (PR2): recorrer las anotaciones de
las funciones públicas, comprobar que ninguna nombra los tipos prohibidos, y contar cuántas firmas
se revisaron (PR3).

---

## 3. Cómo se escribe un paso

### S1 · El paso hace una cosa y lo dice en la primera línea

El docstring empieza por el número de paso, si es determinista y la capacidad que cubre, y sigue con
una frase de qué hace:

```python
"""Paso 6 de Analyze · determinista · `cap. 16a, 42a`.

Leer las rutas y versiones efectivas de las herramientas de build.
"""
```

### S2 · El número de paso va en el docstring, nunca en el nombre del archivo

El código lo explica: «los números caducan en cada renumeración del maestro». Un
`step_06_read_tools.py` obliga a renombrar archivos cada vez que se inserta un paso.

### S3 · Un paso no declara tipos, no anida funciones y no se queda en firma

Las tres cosas están **verificadas por pruebas** que recorren los 213 archivos. Los tipos viven en
`models/`; una función anidada dentro de otra es un paso que no se dividió (y además no se puede
importar ni probar); y un paso que todavía levanta `NotImplementedError` es una firma, no código.

### S4 · Se pregunta, no se deduce

```python
def _version(runnable: str, flag: str) -> str:
    """La versión que la herramienta dice de sí misma. Se pregunta; no se deduce del nombre."""
```

### S5 · Lo que el paso NO hace se escribe igual que lo que hace

Los docstrings más útiles del ejemplo delimitan: «NO CLASIFICA, NO DECIDE, NO BIFURCA», y explican
qué capacidad quedó obsoleta y por qué. Delimitar evita que el siguiente añada la rama que ya se
decidió no tener.

### S6 · Los efectos secundarios son explícitos en el nombre *(ya se cumple)*

El nombre de una función dice si toca el mundo. Es la costumbre más sólida del código de ejemplo:
sus 213 pasos se llaman `read_*`, `write_*`, `verify_*`, `detect_*`, `freeze_*`, `inventory_*`,
`compose_*`, y los predicados `is_*`, `are_*`, `did_*`, `has_*`.

Tres exigencias concretas:

- Una función que escribe en disco se llama `write_*` o `save_*`, **nunca** `get_*` o `load_*`.
- Una función que devuelve un booleano se llama con un prefijo de predicado.
- Un módulo **no tiene efectos secundarios al importarse**: nada de I/O en el top-level (ver P5).

Esto es **verificable**, y debe verificarse con una prueba estructural como las que el ejemplo ya
tiene (ver PR2): recorrer los archivos de `steps/`, comprobar que el único nombre de `__all__` empieza
por uno de los verbos permitidos, y contar cuántos se encontraron (PR3).

```python
# MAL · lee, escribe y no lo dice
def get_report(path): path.write_text(render()); return path

# BIEN · el nombre declara el efecto
def write_report(path: Path) -> Path: ...
```

### P4 · Las funciones no mutan sus argumentos *(ya se cumple)*

Si una función recibe un `dict` o una `list`, no los modifica: devuelve un valor nuevo. La mutación
de argumentos es un efecto secundario oculto que produce bugs difíciles de rastrear.

Excepción legítima, y así aparece en el ejemplo: una función cuyo **propósito declarado** es
escribir en una estructura del llamador (`apply_propagation(captured, target)`) puede hacerlo, pero
entonces el nombre lo dice, el docstring lo dice, y es el único punto donde ese acto ocurre.

### P8 · Las funciones internas llevan prefijo `_` *(ya se cumple)*

Si una función no forma parte de la API pública del módulo, su nombre empieza con `_`. Es un
contrato con el lector, no solo una convención. En este código la convención es más estricta: **una
función pública por archivo** (la que nombra `__all__`) y las privadas que hagan falta, a nivel de
módulo, no anidadas.

### P2 · Captura solo las excepciones que esperas *(ya se cumple)*

`except Exception` está prohibido salvo en puntos de entrada de alto nivel (`main()`) o en
degradaciones justificadas con un comentario que diga *por qué*. En los demás casos, captura el tipo
concreto. Si la excepción indica un bug del programador (`AttributeError`, `TypeError`, un `KeyError`
en un dict que debería tener esa clave), no la captures: deja que burbujee.

```python
# BIEN · tal como lo hace el verificador de contratos
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as err:
    add(f"{spec.name}.keys", f"{path.name} no se pudo parsear: {err}")
    continue
```

### P3 · Sin `SystemExit` fuera de `main()` *(ya se cumple)*

Las funciones de dominio lanzan excepciones de dominio. Solo `main()` las convierte en `sys.exit()`.
Así cualquier función es invocable desde una prueba o desde otro módulo sin que el proceso muera.

### P5 · Sin I/O ni cómputo pesado en el top-level del módulo *(ya se cumple)*

Las variables de módulo valen para constantes puras y para declaraciones literales (un
`ANALYZE_CONTRACT`, un `ORDER`). No valen para resultados de I/O ni de cómputo pesado: generan
efectos al importar y hacen el módulo no probable de forma aislada.

```python
# MAL · lee disco al importar
_SCHEMA = _load_schema()

# BIEN · cargado en el punto de uso
def main() -> None:
    schema = load_schema()
```

### P7 · Devuelve tipos coherentes *(ya se cumple)*

Una función devuelve siempre el mismo tipo. Las tuplas `(bool, dict)` donde el significado del dict
cambia según el bool son contratos frágiles. Usa una dataclass, un `NamedTuple`, o `None` cuando no
hay resultado.

El ejemplo devuelve `tuple[Finding, ...]` en todas las comprobaciones, vacía cuando no hay nada que
reportar, y nunca `None` para decir «todo bien». Y cuando devuelve un par lo hace con significado
fijo: `_dig()` devuelve `(encontrada, valor)`, donde el primer elemento distingue «ausente» de
«presente valiendo `null`», que no son lo mismo.

### P10 · Los comandos externos se construyen con listas *(ya se cumple)*

Nunca por concatenación de strings: se rompe con valores que llevan espacios y es difícil de
auditar.

```python
cmd = ["mvn", "dependency:tree", "-DoutputFile", str(output)]
if offline:
    cmd.append("--offline")
subprocess.run(cmd, check=True)
```

---

## 4. Tipos, constantes y presupuestos

### T1 · `StrEnum` para los conjuntos cerrados que también se leen como texto

Los cinco procesos son un `StrEnum`, no cadenas sueltas. El razonamiento del código: «una cadena
suelta no dice de qué familia es», así que un nombre mal escrito «no falla: se comporta como un
proceso que no existe y toma la rama de ninguno».

`StrEnum` y no `Enum` cuando el mismo valor tiene que leerse como dato desde fuera del intérprete
(un JSON, un output de workflow). `Enum` a secas cuando no sale del proceso.

No basta con decir «usa un enumerado»: lo que decide entre los dos es si el valor tiene que
leerse como texto fuera del intérprete.

### T2 · Dos familias parecidas no se fusionan

El ejemplo mantiene `Process` y `WorkspaceMode` separados aunque compartan cuatro valores, porque no
son lo mismo. Confundirlas «era fácil precisamente por ser cadenas».

### T3 · Una lista que no debe crecer sola no se genera

```python
ORDER: tuple[Process, ...] = (Process.ANALYZE, Process.PLAN, Process.MIGRATE, Process.VALIDATE)
```

Se escriben los miembros y no `tuple(Process)`, y el docstring dice por qué: «un día alguien añade
un proceso al enumerado y esta tupla no debe crecer sola».

### T4 · El presupuesto lo decide quien tiene la vista, y baja por la firma sin valor por defecto

La regla más distintiva del ejemplo. `OUTPUT_ATTEMPTS` estaba escrito como literal en los cuatro
nodos; ahora lo decide el orquestador y **se pasa como argumento sin default**:

> Con un default en la firma, un nodo llamado desde otro sitio volvería a decidir por su cuenta y
> **la omisión y la decisión se escribirían igual**.

El mismo criterio vale para cualquier campo cuya ausencia de valor cambiaría el enrutado:
`Finding.owner` no tiene default porque la discriminación entre reintentar y escalar depende de él.

### T5 · Los presupuestos que cuentan cosas distintas no se llaman parecido

`MAX_RETRY` (vueltas del circuito), `OUTPUT_ATTEMPTS` (intentos de contrato de salida) y
`max_attempts` (bucle de autocuración) se documentan juntos con un apartado explícito de «qué no
es», precisamente porque se confunden.

### T6 · Todo umbral, tope, timeout, ronda o top-N es una constante nombrada *(ya se cumple)*

Cualquier número que sea una **palanca de comportamiento** vive como constante nombrada
(`UPPER_SNAKE_CASE` a nivel de módulo, o campo de una dataclass de configuración), nunca como literal
incrustado en la lógica. El nombre explica *qué controla* y su valor se cambia en un solo lugar.

Incluye los **límites de truncado de contexto de prompts** (`[:4000]`, `[:8000]`), que son decisiones
de diseño con impacto directo en la calidad de las respuestas y no deben aparecer como literales
dentro de una función de render.

El **valor por defecto de un flag de CLI** que expone una de estas palancas se toma de la misma
constante; no se re-teclea el número en `argparse`.

Excepción: literales sin significado de dominio (`0`, `1`, `-1` como índices o incrementos triviales).

```python
# MAL
if len(cases) >= 7: stop()
parts.append(f"CONTEXTO:\n{context[:4000]}")

# BIEN
MAX_EVAL_CASES = 7            # tope de casos por suite (acota el coste de validar)
MAX_CONTEXT_CHARS = 4_000     # ajustar si el modelo objetivo tiene ventana mayor
```

---

## 5. Imports

### I1 · `from __future__ import annotations` en todos los módulos

### I2 · Lo que solo se usa para tipar va en `TYPE_CHECKING`

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from migration.transform.commons.paths import CircuitPaths
```

El `# pragma: no cover` es sistemático: ese bloque no se ejecuta y no debe contar como descubierto.

### I3 · `__all__` explícito en cada módulo

Un solo nombre en los pasos; la lista ordenada en los módulos de contrato.

### I4 · Import por nombre completo, sin alias creativos

El ejemplo importa `from ...steps.freeze_context import freeze_context`. Las líneas quedan largas y
se parten con paréntesis, pero se puede buscar el nombre y encontrarlo.

### P1 · Todos los imports al inicio del módulo *(ya se cumple)*

Nunca dentro de funciones ni de bloques condicionales, tampoco los de stdlib. La única excepción
admitida es un import de una dependencia opcional que no todos los consumidores del módulo traen en
su camino, y entonces se escribe el motivo justo encima:

```python
# EL IMPORT VA DENTRO Y NO ARRIBA. Este módulo lo importan los cinco procesos y no todos traen
# pydantic en su camino.
from pydantic import BaseModel  # noqa: PLC0415
```

Sin ese comentario, un import dentro de una función es un incumplimiento.

---

## 6. Comentarios, docstrings e idioma

### D1 · El comentario explica por qué, y sobre todo por qué NO

Es lo que más distingue a este código. No se comenta lo que hace la línea: se comenta la decisión, y
muy a menudo la decisión **descartada**:

```python
# EL ENTRY POINT DEL JOB NO SE DECLARA AQUÍ, y no es un olvido.
# ... y las dos mitades eran falsas: ese módulo no existe, y el workflow no llama a un comando
# instalado sino al archivo por su ruta.
```

Corolario: un comentario que explica *qué* hace el código es señal de que el nombre o la estructura
son insuficientes. Arregla el nombre, no añadas el comentario.

### D2 · Una corrección deja constancia de dónde se midió

```python
# Decía «de dos cosas». Corregido al revisar el paso 15 de Plan.
```

No es ceremonia: es lo que impide que el siguiente reintroduzca el error creyendo que corrige un
descuido.

### D3 · El docstring del módulo tiene secciones y cita su fuente

`Por qué existe`, `Qué cubre y qué no`, `Trazabilidad`, `Referencias`, con las capacidades y los
documentos de diseño concretos. Un lector nuevo sabe de dónde salió cada exigencia.

### D4 · Si algo está sin pinear, sin decidir o pendiente, se dice en el sitio

```python
# SIN PIN, y es deliberado hasta que se resuelva una pregunta abierta: el informe E2 dice medir
# «con lizard» pero no declara con qué versión.
```

### D5 · El código se escribe en inglés; la prosa, en español *(ya se cumple)*

Los **identificadores** van en inglés: módulos, clases, funciones, variables, constantes, enums, ids
de job y nombres de paso. La **prosa** sigue en español: comentarios, docstrings, mensajes al
usuario, resúmenes de CI y documentación.

La razón no es estética: el contrato de datos ya está en inglés, así que el código en español sería
la incoherencia. Un `en_marketplace` junto a un `superseded_by` obliga a recordar en qué idioma se
llamó cada cosa.

**Los nombres de las pruebas son prosa, no identificadores** (ver PR1): siguen en español. En el
código de ejemplo los **nombres de archivo** de las pruebas también están en español
(`test_bandas_de_precalculo.py`); es la única desviación conocida y no se propaga: los archivos
nuevos van en inglés.

**Excepción dura, lo que no se traduce nunca**, porque son contratos que se emparejan por texto:

- Los **cuatro identificadores del gate** de `agentes-sdlc` (`conformidad`, `validar`,
  `comportamiento`, `Veredicto de comportamiento`). Son comprobaciones requeridas del ruleset, y
  renombrar cualquiera deja todas las solicitudes de cambio bloqueadas para siempre, esperando un
  estado que nadie volverá a emitir. Ya ocurrió dos veces.
- Los **cinco workflows reutilizables** (`validar`, `evaluar`, `publicar`, `etiquetar`,
  `promocionar`): otros repositorios los referencian con `uses: …@main`.
- Las **claves ya persistidas** en Port o en los esquemas: renombrarlas no es renombrar, es migrar.

Aplica al código nuevo. No dispara una migración masiva del existente.

---

## 7. Errores

### X1 · Los errores de dominio tienen una jerarquía propia

Define una excepción base del dominio y subclases por categoría. Eso permite capturar a distintos
niveles de granularidad sin recurrir a `except Exception`: `main()` captura la base, y las funciones
concretas capturan solo la rama que les incumbe.

**El defecto que corrige, medido aquí.** Hoy el código de ejemplo tiene **tres bases sin relación
entre sí**:

| Excepción | Base | Dónde |
|---|---|---|
| `ProvisionError` | `RuntimeError` | `provision/artifactory_trust.py` |
| `InvocationFailed` | `RuntimeError` | `transform/commons/agent_invocation.py` |
| `CircuitEscalation` | `Exception` | `transform/commons/escalation.py` |

No hay ningún punto desde el que se puedan capturar las tres sin nombrarlas una a una ni caer en
`except Exception`, y la tercera ni siquiera comparte base con las otras dos. Cuando se añada la
cuarta, el `except` de `main()` habrá quedado incompleto sin que nada lo avise.

```python
# exceptions.py · módulo compartido
class MigrationError(Exception):
    """Base del dominio. Captura todo lo nuestro sin capturar bugs."""

class ProvisionError(MigrationError): ...
class InvocationFailed(MigrationError): ...
class CircuitEscalation(MigrationError): ...
```

### X2 · Una comprobación devuelve hallazgos; una imposibilidad lanza

El ejemplo separa las dos cosas y merece copiarse: las funciones de contrato devuelven
`tuple[Finding, ...]` y **quien llama decide qué hacer**. Esa distinción es la que permite que el
mismo código sirva a los dos extremos de la costura (la salida del productor y la entrada del
consumidor), cambiando solo a quién se atribuye el hallazgo. Una excepción se reserva para lo que
impide continuar, no para reportar un incumplimiento previsto.

---

## 8. Logging

Esta sección cubre **la mayor carencia del código de ejemplo**: 391 módulos sin una sola línea de
`logging`. Todo el diagnóstico existente es lo que quede en excepciones y en hallazgos.

Los **25 `print` actuales están en tres archivos** (`provision/artifactory_trust.py`,
`provision/artifactory_trust_local.py`, `check_contracts.py`) y son **salida legítima de CLI**, no
diagnóstico: son lo que el operador lee o lo que otro proceso consume. Esos `print` se quedan (ver
L1 y L8). Lo que falta es el logging, que es otra cosa y va a otro sitio.

El logging es observabilidad permanente, no andamiaje temporal. Un mensaje que se añade para
depurar y luego se borra indica que el sistema de logging no estaba bien definido.

### L1 · Usa `logging` de stdlib, nunca `print` para diagnóstico

`print` está reservado a la salida que el caller espera consumir: el informe que imprime
`check_contracts`, el JSON que otro proceso lee, el texto que se redirige. Todo lo demás (progreso,
advertencias, errores internos, detalle de depuración) usa `logging`.

```python
# MAL · diagnóstico por print
print(f"Error procesando {item}: {exc}", file=sys.stderr)

# BIEN
log.error("Error procesando item %s", item, exc_info=exc)
```

### L2 · Un logger por módulo, nombrado con `__name__`

```python
import logging

log = logging.getLogger(__name__)
```

`__name__` produce jerarquías automáticas que permiten filtrar por módulo desde la configuración,
sin tocar el código. Nunca uses el root logger (`logging.warning(...)`) desde un módulo de librería.

### L3 · Usa el nivel correcto para cada tipo de mensaje

| Nivel | Cuándo usarlo |
|---|---|
| `DEBUG` | Detalles internos útiles solo para diagnosticar un bug concreto: valores de variables, rutas intermedias, decisiones de ramificación |
| `INFO` | Eventos normales que confirman que el sistema funciona: inicio de un paso, artefacto escrito, intento concedido |
| `WARNING` | Algo inesperado que no impide continuar: archivo opcional ausente que activa el modo alternativo, hallazgo no bloqueante |
| `ERROR` | Fallo que aborta una operación, no el proceso: excepción capturada, contrato de salida incumplido |
| `CRITICAL` | Fallo que hace imposible continuar: no se puede inicializar, dependencia crítica ausente |

### L4 · Configura el logging una sola vez, en `main()`

Los módulos de librería **nunca** configuran el logging: solo lo usan. Un módulo que llama a
`logging.basicConfig()` o añade handlers rompe la configuración del proceso que lo importa.

### L5 · Todos los CLIs tienen el flag `--verbose` / `-v`

Activa `DEBUG`; sin él, el nivel es `INFO`. Esto reemplaza el patrón de añadir y quitar prints
temporales: los mensajes de depuración siempre están en el código, solo se encienden cuando hacen
falta.

```python
ap.add_argument("--verbose", "-v", action="store_true",
                help="Activa logging DEBUG (detalles internos de ejecución).")
```

### L6 · Loggea excepciones con `exc_info=True`, no con f-strings manuales

```python
# MAL · pierde el traceback
log.error("Error: %s: %s", type(exc).__name__, exc)

# BIEN
log.error("Fallo al procesar %s", item_id, exc_info=True)
```

### L7 · Los mensajes de log usan `%s`, no f-strings

`logging` aplica el formato de forma perezosa, solo si el mensaje va a emitirse. Con f-strings la
cadena se construye siempre, aunque el nivel esté apagado.

```python
log.debug("pasos=%s", [s.name for s in steps])
```

### L8 · Separa la salida estructurada del logging

La salida que otro proceso consume va a `stdout` con `print`. El logging va siempre a `stderr`. Las
dos corrientes no se mezclan. Es exactamente la línea que separa los 25 `print` actuales (stdout,
legítimos) de lo que hay que añadir (stderr, logging).

### L9 · El formato del log se adapta al entorno

En CI, formato plano y sin colores para que sea parseable; en desarrollo puede llevar marca de
tiempo. La detección del entorno ocurre en la función que configura el logging, nunca en un módulo
de librería.

```python
def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    in_ci = os.getenv("CI") == "true"
    fmt = ("%(levelname)-8s %(name)s · %(message)s" if in_ci
           else "%(asctime)s %(levelname)-8s %(name)s · %(message)s")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)
```

---

## 9. Prompts

El proyecto no centraliza prompts en un `prompts.py`. Resuelve el problema un nivel más arriba, y es
mejor: **el prompt se genera desde el contrato del nodo**.

### PM1 · El prompt se deriva de la declaración, no se escribe a mano

`build_agent_prompt(ANALYZE_CONTRACT, context_block, findings)` compone tres bloques: la corrección
dirigida, la evidencia y el contrato de salida renderizado por `describe_contract_for_prompt()`. El
motivo está escrito en el código:

> Existe para que **lo que se le pide a la invocación y lo que después se le verifica salgan de la
> misma declaración**. Si se escribieran por separado podrían divergir, que es exactamente la deriva
> que este contrato previene.

El paso que lo usa lo repite: «lo que aquí se pide y lo que los pasos 35 a 38 comprueban salen de la
misma declaración». Centralizar cadenas de texto en un módulo no da eso: dos cadenas centralizadas
divergen igual de bien que dos dispersas.

Consecuencia práctica: si hay que pedirle algo nuevo al modelo, se añade al contrato, no al prompt.

### PM2 · Una sola función de render, con la variación por parámetro

La primera invocación y la correctiva son **la misma llamada** con el bloque de hallazgos vacío o
lleno. No se parte en `render_prompt` y `render_prompt_correctivo`: sería duplicar una capacidad para
expresar un argumento opcional. Y el parámetro tiene que estar en la firma aunque la primera vuelta
lo deje vacío, porque sin él el reintento sería literalmente la misma llamada, y entonces no es una
corrección sino una repetición.

### PM3 · Al prompt solo entra lo que el modelo tiene que juzgar

El bloque de contexto **no es un volcado del sello: es una proyección de él**, y qué entra se deriva
de lo que los pasos declaran juzgar o redactar. El motivo no es el coste: «darle evidencia que no
tiene que juzgar es ponerle delante material sobre el que podría actuar sin que nadie se lo haya
pedido».

Lo mismo por el otro lado en el bloque correctivo: solo entran los hallazgos que la invocación de
ese nodo puede reparar. Un hallazgo de otro dueño solo consigue que intente arreglar algo que no está
en su mano.

### PM4 · El formato de respuesta esperado se documenta junto al prompt

El prompt que pide una respuesta en cierto formato y el código que la parsea son un contrato. Si el
formato cambia en el prompt pero no en el parser, el fallo es silencioso. La documentación del
formato va como comentario inmediatamente antes de la constante o de la función de render. Si la
respuesta se parsea a un modelo pydantic, ese modelo es la documentación viva del contrato y se cita
por su nombre.

### PM5 · Los límites de truncado son constantes nombradas

Ver T6. `[:4000]` dentro de una función de render es una decisión de diseño escondida en un literal.

---

## 10. Pruebas

### PR1 · El nombre de la prueba es una frase que describe el defecto

```python
def test_la_entrada_rechaza_cuando_falta_el_entregable_del_anterior(node, workspace) -> None: ...
def test_el_frente_no_traga_una_categoria_mal_escrita() -> None: ...
def test_las_coordenadas_se_leen_del_pom_y_no_por_grep(tmp_path) -> None: ...
```

El nombre es lo único que se lee cuando la prueba falla en CI. `test_revisar_paso_3` no dice nada.

### PR2 · La arquitectura se prueba, no solo se documenta

Hay pruebas que recorren el código fuente y verifican su forma: que ningún paso siga siendo una
firma, que cada paso exporte una sola función, que ninguno declare un tipo, que ninguno anide
funciones. **Una regla de estructura sin prueba es una recomendación.** Las reglas E4, S3 y S6 son
candidatas obvias.

### PR3 · Toda prueba que recorre archivos cuenta cuántos encontró

```python
STEPS = 213

def test_son_doscientos_trece() -> None:
    assert len(found) == STEPS, "o falta alguno, o el recorrido dejó de mirar donde tenía que mirar"
```

El motivo lo dice el propio archivo, y es la mejor frase del repositorio: **«una regla verde y una
muerta se ven igual»**. Sin el recuento, un `rglob` que deja de encontrar archivos pasa en verde sin
mirar nada.

### PR4 · Lo que ya comprueba un comando se comprueba también en la suite

El grafo de contratos tiene su propio comando, y además una prueba de una línea que lo llama: «un
desarrollador no ejecuta un comando que no conoce, pero sí ejecuta la suite antes de empujar».

### PR5 · El mensaje de la aserción dice qué hacer, no qué falló

Las aserciones llevan mensaje con el conteo, los primeros elementos y la interpretación de las
causas posibles.

Corolario: una prueba comprueba **una cosa**, y su fallo señala una sola causa. Si el caso tiene
varias variantes, se recorren en un bucle con el valor en el mensaje de la aserción, para que el
fallo diga cuál.

### PR6 · Los dobles se inyectan por argumento, no con `monkeypatch`

Si la función recibe su dependencia externa como argumento (con un default sobreescribible cuando
haga falta), la prueba sustituye el doble y no hace falta parchear módulos. El *monkeypatching* es
una señal de que el cableado está escondido dentro de la función en vez de estar en la firma.

```python
# MAL · la prueba conoce la implementación interna
def test_validar(monkeypatch):
    monkeypatch.setattr("migration.transform.adapters.repository.read", lambda *_: FAKE)

# BIEN · la dependencia es un argumento
def validate(root: Path, *, repository=repository_adapter) -> Result: ...

def test_la_validacion_usa_lo_que_le_da_el_repositorio():
    assert validate(Path("."), repository=FakeRepository()).is_conformant
```

Ojo con T4 de esta misma norma: **un presupuesto no lleva default**. La inyectabilidad con default
vale para adaptadores, no para palancas de comportamiento.

### PR7 · El código que decide si algo se publica tiene sus propias pruebas en CI

Un validador, un gate, un comprobador de contratos o un generador de índice son infraestructura de
la que dependen todos los consumidores: si se rompen en silencio, dejan de proteger sin que nadie lo
note. Sus pruebas corren en cada cambio que los toque.

```yaml
on:
  pull_request:
    paths: ["src/migration/**", "tests/**"]

jobs:
  pruebas:
    steps:
      - name: Ejecutar la suite de contratos y estructura
        run: python -m pytest tests -q
```

---

## 11. Empaquetado

### EP1 · `py.typed`, y se explica para qué

Sin el marcador PEP 561, «un verificador de tipos IGNORA el paquete entero», y toda la maquinaria de
contratos tipados solo comprobaría en ejecución.

### EP2 · Las dependencias de prueba van en un extra

Con el motivo escrito: ningún paso las usa, y arrastrarlas al runner sería «meter en el job una
dependencia que nadie invoca».

### EP3 · Los recursos que el runner necesita se declaran o no llegan

`package-data` lleva el certificado, y el comentario advierte que «lo que no se declare aquí no llega
al runner».

### EP4 · No se declara un entry point que no existe

El ejemplo retiró uno que llevaba tiempo reventando al invocarlo, y dejó escrito el diagnóstico:
había «tres declaraciones del mismo entry point y solo dos coincidían».

---

## 12. YAML / GitHub Actions

Esta sección es ortogonal al resto: el código de ejemplo no dice nada de workflows, y los workflows
son el otro lugar donde la duplicación silenciosa hace daño.

### Y1 · La lógica reutilizable entre workflows vive en composite actions

Si dos workflows comparten lógica (instalación de dependencias, configuración de entorno, pasos de
validación), esa lógica vive en `.github/actions/<nombre>/action.yml` y los workflows la invocan con
`uses:`. Ninguna versión de herramienta ni parámetro de configuración se repite en dos archivos.

### Y2 · Las versiones de herramientas son variables, no literales

```yaml
# MAL
run: npm install -g my-tool@1.2.3

# BIEN
env:
  TOOL_VERSION: "1.2.3"
run: npm install -g my-tool@${{ env.TOOL_VERSION }}
```

Si la misma versión aparece en más de un workflow, vive en un composite action o en una variable de
repositorio.

### Y3 · Las variables derivadas de inputs se resuelven una sola vez

Si `${{ github.event.inputs.X || 'default' }}` aparece más de una vez en un job, resuélvelo en un
step inicial o como `env` del job.

### Y4 · Las ramas condicionales complejas son steps separados con `if:`

Si un `run` contiene más de un `if/elif/else` de bash, o si la condición depende de outputs de steps
anteriores, divide en steps con `if:` de Actions. Cada rama tiene un nombre visible en la UI.

```yaml
- name: Transform · PR, alcance acotado por diff
  if: github.event_name == 'pull_request'
  run: tool --scope "${{ steps.scope.outputs.items }}"

- name: Transform · manual, todos los microservicios
  if: github.event_name == 'workflow_dispatch' && github.event.inputs.all == 'true'
  run: tool --all
```

### Y5 · Los paths son absolutos o consistentes con su `working-directory`

Cuando un step escribe en un path y otro lee de él, ambos usan la misma expresión. Mezclar paths
relativos con distintos `working-directory` genera bugs silenciosos donde el directorio existe pero
está vacío.

```yaml
- name: Transform
  working-directory: src/migration
  run: tool --output "$GITHUB_WORKSPACE/reports"

- name: Leer los resultados
  run: cat "$GITHUB_WORKSPACE/reports/output.json"
```

### Y6 · Los steps con `continue-on-error` registran su outcome

Si un step usa `continue-on-error: true`, su outcome se captura y se propaga (al mensaje de commit,
al summary o a un output del job). Un fallo silencioso que no deja rastro es un problema de
observabilidad.

### Y7 · Las exclusiones en globs son explícitas con `!`

```yaml
# MAL · excluye por la profundidad del glob
path: reports/*/*.json

# BIEN
path: |
  reports/*/*.json
  !reports/meta.json
```

### Y8 · Los nombres de steps describen el resultado y el contexto

Un step llamado `Run` o `Install` no distingue entre instancias del mismo tipo. El nombre debe ser
autoexplicativo en la UI sin abrir el log: `Install dependencias del proveedor (${{ env.PROVIDER }})`,
`Checkout histórico de resultados (read-only)`.

---

## 13. Checklist de revisión

**Estructura**
- [ ] El paquete está bajo `src/` y el adaptador de la línea de órdenes fuera del paquete. (E1)
- [ ] Cada proceso tiene las mismas cuatro bandas, con `steps/` y un archivo por paso. (E2, E4)
- [ ] Los archivos que componen no calculan ni bifurcan. (E3)
- [ ] Cada paso exporta una sola función. (E4)
- [ ] Lo compartido está en el `commons/` del nivel que le toca, ni más arriba ni más abajo. (E5)
- [ ] Ningún módulo agrupa más de una responsabilidad; ninguno cruza ~300 líneas en silencio. (E6)

**Contratos**
- [ ] Cada nodo declara su contrato en un archivo aparte del código que lo cumple. (C1)
- [ ] Pydantic en la frontera exterior; `dataclass(frozen=True, slots=True)` para lo que viaja dentro. (C2)
- [ ] Nada se parsea dos veces: se transporta el modelo. (C3)
- [ ] Cada convención (rutas, nombres) se escribe una sola vez. (C4)
- [ ] Hay una comprobación que cruza lo declarado con lo implementado sin ejecutar. (C5)
- [ ] Cada clave del contrato declara quién la lee. (C6)
- [ ] El verificador nombra y enruta; no repara. (C7)
- [ ] Ninguna firma declara `dict`, `Mapping`, `object` ni `Any` para datos del dominio. (C8)
- [ ] Los tipos viven en el `commons/models/` que les toca, y los conjuntos cerrados son enumerados. (C8, T1, E5)

**Pasos y funciones**
- [ ] El docstring abre con número, determinismo y capacidad. (S1)
- [ ] El número de paso no está en el nombre del archivo. (S2)
- [ ] Ningún paso declara tipos, anida funciones ni queda en `NotImplementedError`. (S3)
- [ ] El docstring dice también lo que el paso NO hace. (S5)
- [ ] El nombre declara el efecto: `write_*`/`save_*` para lo que escribe, `is_*`/`has_*` para predicados. (S6)
- [ ] Ninguna función muta sus argumentos, salvo que mutar sea su propósito declarado. (P4)
- [ ] Las funciones internas llevan prefijo `_` y están a nivel de módulo. (P8)
- [ ] No hay `except Exception` sin justificación escrita. (P2)
- [ ] No hay `SystemExit` fuera de `main()`. (P3)
- [ ] No hay I/O ni cómputo pesado en el top-level. (P5)
- [ ] Los tipos de retorno son coherentes; no hay `tuple[bool, X]` con semántica variable. (P7)
- [ ] Los comandos externos se construyen con listas. (P10)

**Tipos y presupuestos**
- [ ] Los conjuntos cerrados son `StrEnum` (o `Enum` si no salen del proceso), no cadenas. (T1)
- [ ] Dos familias parecidas siguen separadas. (T2)
- [ ] Las listas que no deben crecer solas se escriben con sus miembros. (T3)
- [ ] Los presupuestos se deciden donde se tiene la vista y bajan por la firma **sin default**. (T4)
- [ ] Los presupuestos que cuentan cosas distintas no se llaman parecido. (T5)
- [ ] Umbrales, topes, timeouts, rondas, top-N y truncados son constantes nombradas. (T6)

**Imports**
- [ ] `from __future__ import annotations` en todos los módulos. (I1)
- [ ] Lo que solo se usa para tipar va en `TYPE_CHECKING` con `# pragma: no cover`. (I2)
- [ ] `__all__` explícito. (I3)
- [ ] Import por nombre completo, sin alias. (I4)
- [ ] Todos los imports al inicio; el que no, lleva su motivo escrito encima. (P1)

**Comentarios e idioma**
- [ ] Los comentarios explican por qué, y por qué no. (D1)
- [ ] Las correcciones dejan constancia de dónde se midieron. (D2)
- [ ] El docstring del módulo tiene secciones y cita su fuente. (D3)
- [ ] Lo pendiente o sin decidir se dice en el sitio. (D4)
- [ ] Identificadores en inglés, prosa en español; sin tocar los cuatro identificadores del gate, los cinco workflows reutilizables ni las claves persistidas. (D5)

**Errores**
- [ ] Los errores de dominio cuelgan de una única excepción base del proyecto. (X1)
- [ ] Las comprobaciones devuelven hallazgos; solo lo que impide continuar lanza. (X2)

**Logging**
- [ ] No hay `print` de diagnóstico; los `print` que quedan son salida que alguien consume. (L1, L8)
- [ ] Cada módulo tiene `log = logging.getLogger(__name__)`. (L2)
- [ ] El nivel de cada mensaje es el correcto. (L3)
- [ ] El logging se configura una sola vez en `main()`. (L4)
- [ ] Todos los CLIs tienen `--verbose` / `-v`. (L5)
- [ ] Las excepciones se loggean con `exc_info=True`. (L6)
- [ ] Los mensajes usan `%s`, no f-strings. (L7)
- [ ] La salida estructurada va a `stdout`; el logging a `stderr`. (L8)
- [ ] El formato se decide por entorno, dentro de la función de configuración. (L9)

**Prompts**
- [ ] El prompt se genera desde el contrato; nada que se le pida al modelo está escrito solo en el prompt. (PM1)
- [ ] Una sola función de render, con la variación por parámetro. (PM2)
- [ ] Al prompt solo entra lo que el modelo tiene que juzgar o puede reparar. (PM3)
- [ ] El formato de respuesta esperado está documentado junto al prompt. (PM4)
- [ ] Los límites de truncado son constantes nombradas. (PM5)

**Pruebas**
- [ ] El nombre de la prueba describe el defecto, en prosa. (PR1)
- [ ] Las reglas de estructura tienen prueba. (PR2)
- [ ] Toda prueba que recorre archivos cuenta cuántos encontró. (PR3)
- [ ] Lo que comprueba un comando se comprueba también en la suite. (PR4)
- [ ] El mensaje de la aserción dice qué hacer; las variantes van en bucle. (PR5)
- [ ] Los dobles se inyectan por argumento, no con `monkeypatch`. (PR6)
- [ ] Validadores, gates y generadores tienen pruebas que corren en CI. (PR7)

**Empaquetado**
- [ ] `py.typed` declarado. (EP1)
- [ ] Dependencias de prueba en un extra. (EP2)
- [ ] Recursos que el runner necesita, declarados. (EP3)
- [ ] Ningún entry point declarado que no exista. (EP4)

**YAML / GitHub Actions**
- [ ] La lógica reutilizable está en composite actions. (Y1)
- [ ] Las versiones de herramientas son variables. (Y2)
- [ ] Los inputs con defaults se resuelven una sola vez. (Y3)
- [ ] Las ramas condicionales complejas son steps con `if:`. (Y4)
- [ ] Los paths son absolutos o consistentes con su `working-directory`. (Y5)
- [ ] Los steps con `continue-on-error` exponen su outcome. (Y6)
- [ ] Las exclusiones de globs son explícitas con `!`. (Y7)
- [ ] Los nombres de steps describen resultado y contexto. (Y8)

---

## 14. Lo que este estándar no adopta, y por qué

Cuatro patrones habituales que aquí quedan fuera. Están escritos para que nadie los introduzca
creyendo que corrige un descuido.

**La arquitectura hexagonal por capas (`domain/`, `application/`, `ports/`, `adapters/`).** Queda
fuera por decisión explícita. Aquí se organiza **por proceso y banda**, y dentro de cada banda por
paso (E2). Las dos disposiciones separan lo puro de lo que toca el mundo, pero por ejes distintos, y
mezclarlas daría una estructura que no se deduce de la ruta, que es justo lo que E2 compra. La
estructura definitiva es una decisión posterior; hasta entonces, se sigue E2.

**Strategy con `Protocol`, Repository y `Protocol` sobre `ABC`.** Los tres empujan hacia la
indirección, y la esencia de este código es la contraria: una función por paso, sin polimorfismo,
sin interfaces con un solo implementador. En 213 pasos no hay ninguna jerarquía de estrategias, y lo
que en otro diseño sería un Repository aquí es un módulo de rutas escrito una sola vez (C4). Una
interfaz con un único implementador es indirección sin beneficio, y aquí la uniformidad la da la
**forma de los archivos**, no una clase base.

**`@dataclass` como respuesta única para los datos estructurados.** No se descarta por estar mal,
sino porque C2 da un criterio más fino: pydantic en la frontera exterior, `dataclass(frozen=True,
slots=True)` para lo que viaja dentro de un proceso, y `NamedTuple` para tuplas pequeñas y
posicionales. «Usa dataclass» no dice dónde acaba la validación y empieza la estructura; C2 sí.

**Centralizar los prompts en un `prompts.py`.** El ejemplo lo resuelve mejor y
está verificado en el código: `build_agent_prompt(ANALYZE_CONTRACT, context_block, findings)` en
`commons/artifact_contract.py`, invocado desde
`analyze/orchestration_sub_process/steps/render_context_into_prompt.py`. El bloque de exigencias del
prompt lo renderiza `describe_contract_for_prompt()` **a partir del mismo `NodeContract` que la banda
de salida verifica**, de modo que lo que se le pide al modelo y lo que se le comprueba después no
pueden divergir. Centralizar cadenas de texto en un módulo no da esa garantía: dos cadenas
centralizadas divergen igual que dos dispersas. Lo que sí se exige, en PM4 y PM5, es documentar el
formato de respuesta esperado y nombrar los truncados: las dos cosas son ortogonales a dónde vive
el prompt.
