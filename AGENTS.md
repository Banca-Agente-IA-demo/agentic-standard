# Reglas de desarrollo de `agentic-standard`

Este archivo lo leen Claude Code y GitHub Copilot CLI cuando el equipo trabaja en este repositorio.
No se distribuye: los plugins de `plugins/` llevan sus propias instrucciones dentro del skill.

Tiene dos partes. La primera son las reglas de arquitectura y código comunes a todo el proyecto. La
segunda, al final, son las reglas específicas de los componentes de este repositorio.

---

# Parte 1. Arquitectura y código limpio

Estas reglas gobiernan todo el código del proyecto: scripts Python, módulos compartidos y workflows de CI/CD en YAML. Son la fuente de verdad para cualquier sesión de Claude Code o Copilot CLI. Aplícalas en cada cambio, sea una función nueva, un refactor o un workflow.

---

## Principios generales (aplican a Python y YAML por igual)

### G1 — Una sola responsabilidad por unidad

Cada función, módulo o job hace **una sola cosa**. Si necesitas la conjunción "y" para describir lo que hace una unidad, divídela.

- Una función que lee datos **no** decide qué hacer con ellos.
- Un step de CI que instala dependencias **no** también ejecuta el proceso principal.
- Un módulo que parsea una estructura **no** también valida las reglas de negocio sobre ella.

#### A nivel de archivo/módulo (el caso más fácil de pasar por alto)

La responsabilidad única aplica al **módulo entero**, no solo a sus funciones. Un archivo donde cada función está bien pero que en conjunto hace de todo sigue violando G1. No te fíes solo del juicio; aplica **dos chequeos explícitos**:

- **Test de la conjunción (para módulos):** si describir el archivo necesita "y" — *"renderiza entradas **y** invoca al juez **y** registra histórico **y** escribe Markdown **y** orquesta"* — está haciendo de más. Cada cláusula es un módulo candidato.
- **Test de grupos de responsabilidad:** si las funciones del archivo caen en más de un grupo temático (p. ej. *parseo*, *juez*, *crítica*, *persistencia*, *reporte*, *orquestación*), cada grupo es candidato a su propio módulo.

#### Disparador de revisión por tamaño (tripwire, **no** límite duro)

Un módulo Python que supera **~300 líneas** es una **señal** —no una falla— de que probablemente acumula más de una responsabilidad. Al cruzar el umbral es **obligatorio** una de dos:

- **(a)** dividirlo en módulos cohesivos, o
- **(b)** dejar un comentario al inicio del archivo justificando *por qué* la cohesión real lo amerita (p. ej. una máquina de estados indivisible).

Nunca se cruza el umbral **en silencio**. El tamaño es solo un *proxy* de la responsabilidad: la regla real es la cohesión (G1), y **la división nunca debe romper una unidad genuina solo para bajar el número** (eso contradiría G3: dividir por la métrica, no por el significado).

#### Extraer un concern no cierra G1 por sí solo

Tras sacar piezas a módulos compartidos (constantes, parsers, prompts, modelos), **vuelve a aplicar los dos tests al núcleo restante**. El archivo que orquesta suele seguir acumulando responsabilidades de ejecución (renderizado, evaluación, persistencia, reporte) que también deben salir; "ya extraje varias cosas" no equivale a "el archivo ya tiene una sola responsabilidad".

### G2 — Sin duplicación (DRY estricto)

Si la misma lógica aparece en dos lugares, extráela. No hay excepciones por "es solo una línea" o "son archivos distintos". La duplicación incluye:

- Bloques de shell idénticos o casi idénticos en workflows distintos.
- Funciones con el mismo propósito en módulos Python distintos.
- Constantes con el mismo valor definidas en más de un lugar.

### G3 — Nombra las cosas por lo que son, no por lo que hacen

Los nombres deben ser autoexplicativos sin necesitar un comentario. Un comentario que explica *qué* hace el código es señal de que el nombre o la estructura son insuficientes. Los comentarios válidos explican *por qué*, no *qué*.

```python
# MAL — el comentario explica el qué
# Calcula si el resultado supera el umbral
ok = value >= threshold

# BIEN — el nombre ya lo dice
above_threshold = measured_value >= pass_threshold
```

### G3b — El código se escribe en inglés; la prosa, en español

Los **identificadores** van en inglés: módulos, clases, funciones, variables, constantes, enums, ids
de job y nombres de paso. La **prosa** sigue en español: comentarios, docstrings, mensajes al usuario,
resúmenes de CI y documentación.

La razón no es estética. El **contrato de datos ya estaba en inglés** —las 13 propiedades del
`envelope.schema.json`, 16 de las 20 del blueprint de Port, y los estados del ciclo de vida
(`conformant`, `certified`, `suspended`)—, así que el código en español era la incoherencia. Un
`en_marketplace` junto a un `superseded_by` obliga a recordar en qué idioma se llamó cada cosa.

```python
# MAL — el identificador en español obliga a traducir mentalmente al cruzar la frontera del esquema
def revisar_envelope(ruta, contenido): ...

# BIEN — identificador en inglés, comentario y mensaje en español
def review_envelope(path: str, content: dict) -> list[Finding]:
    """Comprueba que el envelope declara los siete campos obligatorios."""
```

**Los nombres de las pruebas son prosa, no identificadores.** T2 exige que cada prueba nombre el
defecto que cubre, y eso es una frase: sigue en español. Nadie las importa y `pytest` las descubre
por el prefijo `test_`, que ya es inglés.

**Excepción dura — lo que NO se traduce nunca**, porque son contratos que se emparejan por texto:

- Los **tres requeridos del ruleset** (`verify / rules`, `verify / evals-verdict`,
  `verify / collision`). Renombrar cualquiera deja **todas** las solicitudes de cambio bloqueadas para
  siempre, esperando un estado que nadie volverá a emitir. Ocurrió dos veces en la demo anterior.
- Los **workflows reutilizables** (`register`, `verify`, `tag`, `publish`, `rebuild-index`) y los
  nombres de los jobs de los llamadores: otros repositorios los referencian con `uses: …@v1`.
- El evento `version-published`, las **claves de `GOVERNANCE.json`** y las del blueprint de Port:
  renombrarlas no es renombrar, es migrar.

En esta organización los identificadores nacen en inglés desde el primer commit: no hay código
heredado que migrar ni periodo de transición.

### G4 — Los efectos secundarios son explícitos

Si una función modifica estado externo (escribe un archivo, muta un argumento, modifica variables de entorno), ese efecto debe ser evidente en la firma o en el nombre:

- Una función que muta su argumento debe documentarlo o — mejor — no hacerlo y devolver un valor nuevo.
- Una función que escribe en disco se llama `write_*` o `save_*`, nunca `get_*` o `load_*`.
- Los módulos no tienen efectos secundarios al ser importados (sin I/O en el top-level).

### G5 — Estructura por capas (arquitectura hexagonal)

Mientras G1 dice *qué* hace cada unidad, G5 dice *dónde vive*. El código de un componente se organiza en **paquetes por capa**, no en módulos sueltos en la raíz. El layout estándar (puertos y adaptadores):

- **`domain/`** — entidades y reglas **puras**: sin I/O y sin imports del proyecto fuera de `domain/` (solo stdlib y otros módulos de dominio). Los prompts viven aquí: son lógica de negocio, no configuración (ver *Gestión de prompts*).
- **`application/`** — casos de uso que **orquestan** el dominio a través de puertos.
- **`ports/`** — interfaces (contratos) que la aplicación necesita del exterior.
- **`adapters/`** — todo lo que habla con el exterior (SDKs, filesystem, persistencia, logging): implementan puertos o proveen I/O concreta.
- La **raíz** del componente solo contiene **entry points** (el *composition root*): parsean argumentos, eligen y **cablean** los adaptadores concretos a los puertos, y disparan el caso de uso. Son los únicos que conocen implementaciones concretas.

**Regla de dependencia — la flecha apunta SIEMPRE hacia adentro:**

```
entry point ──▶ application ──▶ ports ◀── adapters
                     │                        │
                     └──────▶ domain ◀────────┘
```

- `domain/` no importa **nada** del proyecto fuera de `domain/`.
- `application/` importa `domain/` + `ports/`. Solo puede importar un módulo concreto de `adapters/` para **I/O de implementación única** que no justifica un puerto (ver abajo); cuando hay polimorfismo, va **siempre** por el puerto.
- `adapters/` implementan/usan `ports/` y tipos de `domain/`; nadie importa un adaptador concreto salvo el composition root (o `application` en el caso pragmático de arriba). **Excepción pragmática (helper de adapter compartido):** un módulo `_`-privado (p.ej. `adapters/_skill_model_query.py`) o un **default inyectable** (que el composition root puede sobreescribir) compartido entre **adapters HERMANOS del MISMO componente** es infra de adapter compartida (DRY, G2), NO acoplamiento de dos implementaciones de puerto → permitido. Sigue prohibido: que un adapter importe la **implementación** de otro puerto, y cualquier import de adapter **entre componentes** distintos (esos cruzan solo por el composition root o por el límite de proceso).
- Los **entry points** son los únicos que instancian adaptadores concretos y los inyectan.

**Puertos solo donde hay polimorfismo real.** Un puerto (interfaz abstracta) se introduce cuando hay —o se anticipa— **más de una implementación** o se necesita un **doble de test** (p. ej. el proveedor de modelo: `claude` / `copilot` detrás del mismo port). Para I/O de **una sola** implementación (leer del filesystem, escribir un JSONL, generar un Markdown), NO se inventa un puerto especulativo: la aplicación llama al módulo concreto de `adapters/` directamente. Una interfaz con un único implementador es indirección sin beneficio (coherente con "no sobre-ingeniería").

**Señales de violación:** un módulo de `domain/` que importa de `adapters/` (la flecha apunta hacia afuera); lógica de negocio acumulada en la raíz del paquete junto a los entry points; un puerto abstracto con una sola implementación que nadie va a intercambiar.

---

## Python

### P1 — Todos los imports al inicio del módulo

Los imports van al principio del archivo, nunca dentro de funciones o bloques condicionales. No hay excepciones para módulos de stdlib.

```python
# MAL — import oculto dentro de una función
def process(data):
    import re
    return re.sub(r"\s+", " ", data)

# BIEN — todos los imports visibles al inicio
import re

def process(data):
    return re.sub(r"\s+", " ", data)
```

### P2 — Captura solo las excepciones que esperas

`except Exception` está prohibido salvo en puntos de entrada de alto nivel (`main()`) o en degradaciones explícitamente justificadas con un comentario de *por qué*. En todos los demás casos, captura el tipo concreto.

```python
# MAL — enmascara bugs del propio código
try:
    data = json.loads(path.read_text())
except Exception:
    return None

# BIEN — solo las excepciones esperadas por razones de dominio
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    return None, f"JSON inválido: {exc}"
except OSError as exc:
    return None, f"No se pudo leer el archivo: {exc}"
```

La regla práctica: si la excepción indica un bug del programador (`AttributeError`, `TypeError`, `KeyError` en un dict que debería tener esa clave), **no** la captures — deja que burbujee.

### P3 — Sin `SystemExit` fuera de `main()`

Las funciones de dominio lanzan excepciones de dominio. Solo `main()` convierte esas excepciones en `sys.exit()`. Esto hace que cualquier función sea invocable desde tests o desde otro módulo sin que el proceso muera.

```python
# MAL — mata el proceso desde una función de dominio
def load_config(path):
    if not path.exists():
        raise SystemExit(f"Configuración no encontrada: {path}")

# BIEN — excepción de dominio; main() decide qué hacer con ella
class ConfigNotFoundError(ValueError):
    """La configuración requerida no existe."""

def load_config(path):
    if not path.exists():
        raise ConfigNotFoundError(f"Configuración no encontrada: {path}")

# En main():
try:
    config = load_config(path)
except ConfigNotFoundError as exc:
    log.error("%s", exc)
    sys.exit(2)
```

### P4 — Las funciones no mutan sus argumentos

Si una función recibe un `dict` o una `list`, no los modifica. Devuelve un valor nuevo. La mutación de argumentos es un efecto secundario oculto que produce bugs difíciles de rastrear.

```python
# MAL — muta el dict del llamador sin que sea evidente
def enrich(record: dict, extra: dict) -> dict:
    record["extra"] = extra   # ← efecto secundario oculto
    return record

# BIEN — devuelve un objeto nuevo; el llamador decide cómo componer
def enrich(record: dict, extra: dict) -> dict:
    return {**record, "extra": extra}
```

### P5 — Sin estado mutable en el top-level del módulo con I/O

Las variables de módulo están permitidas para constantes puras (`MAX_RETRIES = 3`). No están permitidas para resultados de operaciones de I/O o cómputo pesado, porque generan efectos al importar y hacen el módulo no-testeable de forma aislada.

```python
# MAL — lee disco al importar el módulo
_SCHEMA = _load_schema()   # ← efecto al importar; rompe tests aislados

# BIEN — cargado explícitamente en el punto de uso
def main():
    schema = load_schema()
    results = process_all(items, schema=schema)
```

### P6 — Usa tipos de dominio, no magic strings

Los valores que tienen un conjunto finito de opciones válidas son `Enum`, no strings literales. Los magic strings duplicados en múltiples lugares son candidatos inmediatos.

```python
# MAL — strings literales dispersos, un typo es un bug silencioso
if mode == "batch":
    ...
elif mode == "stream":
    ...

# BIEN — enum de dominio, el type checker detecta valores inválidos
from enum import Enum

class ProcessingMode(str, Enum):
    BATCH = "batch"
    STREAM = "stream"

if mode == ProcessingMode.BATCH:
    ...
```

### P7 — Devuelve tipos coherentes

Una función devuelve siempre el mismo tipo. Las tuplas `(bool, dict)` donde el significado del dict cambia según el bool son contratos frágiles. Usa `dataclass`, `NamedTuple`, o devuelve `None` cuando no hay resultado.

```python
# MAL — el significado del segundo elemento depende del primero
def parse(text: str) -> tuple[bool, dict]:
    if invalid:
        return (False, {})
    return (True, {"field": value})

# BIEN — None indica ausencia; dataclass indica presencia con contrato explícito
from dataclasses import dataclass

@dataclass
class ParseResult:
    field: str
    other: int

def parse(text: str) -> ParseResult | None:
    if invalid:
        return None
    return ParseResult(field=..., other=...)
```

### P8 — Las funciones internas llevan prefijo `_`

Si una función no forma parte de la API pública del módulo (no está pensada para ser importada desde fuera), su nombre empieza con `_`. Esto es un contrato con el lector, no solo una convención.

```python
# MAL — aparece como API pública aunque nunca se importe desde fuera
def find_files(directory: Path) -> list[Path]: ...
def count_items(directory: Path) -> int: ...

# BIEN — prefijo _ señala uso interno
def _find_files(directory: Path) -> list[Path]: ...
def _count_items(directory: Path) -> int: ...
```

### P9 — La lógica duplicada entre módulos vive en un módulo compartido

Si dos módulos del proyecto contienen lógica similar (parseo, descubrimiento de archivos, lectura de configuración), esa lógica vive en un módulo compartido. Los consumidores importan desde ahí. Nunca copies y pegues código entre módulos del mismo proyecto.

### P10 — Construye comandos con listas, no con concatenación de strings

Cuando invoques un proceso externo con flags dinámicos (en Python o en shell), usa listas o arrays. La concatenación de strings rompe con valores que contienen espacios y es difícil de auditar.

```python
# MAL — frágil con espacios, difícil de leer
flags = f"--output {output_dir} --format {fmt}"
os.system(f"tool {flags}")

# BIEN — lista explícita, robusta con cualquier valor
cmd = ["tool", "--output", str(output_dir), "--format", fmt]
if verbose:
    cmd.append("--verbose")
subprocess.run(cmd, check=True)
```

### P11 — Los umbrales y límites numéricos son constantes nombradas, no literales mágicos

Cualquier número que sea una **palanca de comportamiento** —un límite, un tope, un umbral, un timeout, un número de rondas/reintentos, un top-N, una tolerancia— vive como **constante nombrada** (`UPPER_SNAKE_CASE` a nivel de módulo, o campo de un `@dataclass` de configuración), nunca como literal incrustado en la lógica. El nombre explica *qué controla* y su valor se cambia en **un solo lugar**. Generaliza PM5 (que ya lo exige para los límites de contexto de prompts) a **todo** el código.

Excepción: literales sin significado de dominio (`0`, `1`, `-1` como índices o incrementos triviales) no necesitan nombre.

```python
# MAL — números mágicos dispersos: ¿qué es 7? ¿por qué 2?
if len(cases) >= 7:
    stop()
for _ in range(2):
    reauthor()

# BIEN — constantes nombradas; el nombre dice QUÉ controla, un solo lugar para ajustar
_MAX_EVAL_CASES = 7           # tope de casos por suite (acota el costo de validate/harden)
_DEFAULT_MAX_ROUNDS = 2       # rondas de re-autoría por skill

if len(cases) >= _MAX_EVAL_CASES:
    stop()
for _ in range(_DEFAULT_MAX_ROUNDS):
    reauthor()
```

El **valor por defecto de un flag de CLI** que expone una de estas palancas se toma de la **misma constante** (no se re-teclea el número en `argparse`): la constante es la única fuente de verdad.

---

## YAML / GitHub Actions

### Y1 — La lógica reutilizable entre workflows vive en composite actions

Si dos workflows comparten lógica (instalación de dependencias, configuración de entorno, pasos de validación), esa lógica vive en un **composite action** (`.github/actions/<nombre>/action.yml`). Los workflows la invocan con `uses:`. Ninguna versión de herramienta ni parámetro de configuración se repite en dos archivos distintos.

```yaml
# .github/actions/setup-tooling/action.yml
name: Setup tooling
inputs:
  tool-version:
    required: true
runs:
  using: composite
  steps:
    - shell: bash
      run: npm install -g my-tool@${{ inputs.tool-version }}
```

### Y2 — Las versiones de herramientas son variables, no literales

Cualquier versión de una herramienta que aparezca en un workflow vive como variable de entorno de nivel de workflow o de job. Si la misma versión aparece en más de un workflow, vive en un composite action o en una variable de repositorio.

```yaml
# MAL — versión hardcodeada, hay que buscarla en todos los archivos para actualizarla
run: npm install -g my-tool@1.2.3

# BIEN — variable en el nivel de job, un solo lugar para cambiarla
env:
  TOOL_VERSION: "1.2.3"

run: npm install -g my-tool@${{ env.TOOL_VERSION }}
```

### Y3 — Las variables derivadas de inputs se resuelven una sola vez

Si el mismo `github.event.inputs.X || 'default'` aparece más de una vez en un job, resuélvelo en un step inicial o como variable de entorno del job. La expresión de resolución se escribe en un solo lugar.

```yaml
# MAL — la expresión con su default se repite en varios steps
run: TOOL="${{ github.event.inputs.tool || 'default-tool' }}"

# BIEN — resuelta una sola vez al nivel del job
jobs:
  build:
    env:
      TOOL: ${{ github.event.inputs.tool || 'default-tool' }}
```

### Y4 — Las ramas condicionales complejas son steps separados con `if:`

Si un step `run` contiene más de un `if/elif/else` de bash, o si la condición depende de outputs de steps anteriores, divide en steps con `if:` de Actions. Cada rama tiene un nombre descriptivo visible en la UI de GitHub.

```yaml
# MAL — lógica de ramificación oculta en bash
- name: Process
  run: |
    if [ "${{ github.event_name }}" = "pull_request" ]; then
      tool --scope "${{ steps.scope.outputs.items }}"
    elif [ "${{ github.event.inputs.all }}" = "true" ]; then
      tool --all
    fi

# BIEN — cada rama es un step nombrado, visible en la UI
- name: Process — PR, scope acotado
  if: github.event_name == 'pull_request'
  run: tool --scope "${{ steps.scope.outputs.items }}"

- name: Process — manual, todos los items
  if: github.event_name == 'workflow_dispatch' && github.event.inputs.all == 'true'
  run: tool --all
```

### Y5 — Los paths son absolutos o consistentes con su `working-directory`

Cuando un step escribe en un path y otro step lee de ese mismo path, ambos usan la misma expresión. Mezclar paths relativos con `working-directory` distintos genera bugs silenciosos donde el directorio existe pero está vacío.

```yaml
# MAL — el path relativo depende del working-directory del step, que puede cambiar
- name: Process
  working-directory: src/runner
  run: tool --output ../reports

- name: Read results
  run: cat reports/output.json   # ¿relativo a qué raíz?

# BIEN — path absoluto, sin ambigüedad entre steps
- name: Process
  working-directory: src/runner
  run: tool --output "$GITHUB_WORKSPACE/reports"

- name: Read results
  run: cat "$GITHUB_WORKSPACE/reports/output.json"
```

### Y6 — Los steps con `continue-on-error` registran su outcome

Si un step usa `continue-on-error: true`, su outcome debe capturarse y propagarse (al commit message, al summary, o a un output del job). Un fallo silencioso que no deja rastro es un problema de observabilidad.

```yaml
# MAL — falla silenciosamente, nada en el log lo refleja
- name: Run process
  continue-on-error: true
  run: tool --all

# BIEN — el outcome se captura y se incluye en el rastro
- name: Run process
  id: process_run
  continue-on-error: true
  run: tool --all

- name: Commit results
  run: |
    OUTCOME="${{ steps.process_run.outcome }}"
    git commit -m "results: ${GITHUB_SHA::7} (status=$OUTCOME)"
```

### Y7 — Las exclusiones en globs son explícitas con `!`

Si un patrón de glob necesita excluir ciertos archivos, la exclusión es explícita con `!`. Las exclusiones implícitas por profundidad de directorio o nombre de archivo se rompen cuando cambia la estructura.

```yaml
# MAL — excluye ciertos archivos implícitamente por la profundidad del glob
path: reports/*/*.json

# BIEN — exclusión explícita y legible
path: |
  reports/*/*.json
  !reports/meta.json
```

### Y8 — Los nombres de steps describen el resultado y el contexto

Un step llamado `Run` o `Install` no dice nada sobre qué caso está manejando. El nombre debe ser autoexplicativo en la UI de Actions sin necesidad de abrir el log.

```yaml
# MAL — genérico, no distingue entre instancias del mismo tipo de step
- name: Run
- name: Install
- name: Checkout

# BIEN — nombre que describe resultado y contexto
- name: Run process — PR, scope acotado por diff
- name: Install dependencias del proveedor (${{ env.PROVIDER }})
- name: Checkout histórico de resultados (read-only)
```

---

## Patrones de diseño orientado a objetos

Estos patrones se aplican **cuando el problema lo justifica**, no por defecto. El criterio siempre es el mismo: ¿esta abstracción reduce complejidad real o la añade? Si la respuesta no es clara, no apliques el patrón.

### OO1 — Usa `@dataclass` para datos estructurados con semántica fija

Cuando una función necesita devolver o recibir varios campos relacionados que siempre viajan juntos, encapsula esos campos en un `@dataclass`. No uses `dict`, `tuple`, o múltiples valores de retorno para datos con estructura estable — son contratos frágiles que el type checker no puede verificar.

**Cuándo aplica:** resultado de parseo, configuración de ejecución, resumen de resultados, cualquier estructura que se pase entre más de dos funciones.

```python
# MAL — tuple con semántica implícita; el orden importa y no se ve
def parse_config(text: str) -> tuple[bool, dict]:
    return (True, {"host": "...", "port": 8080})

# MAL — dict sin contrato; cualquier clave puede faltar
def get_run_options() -> dict:
    return {"timeout": 30, "retries": 3, "verbose": False}

# BIEN — contrato explícito, autocompletado, verificable por el type checker
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    host: str
    port: int

@dataclass
class RunOptions:
    timeout: int = 30
    retries: int = 3
    verbose: bool = False
```

Usa `frozen=True` cuando el objeto no debe mutar después de crearse (configuraciones, resultados).

### OO2 — Usa jerarquías de excepciones para errores de dominio

Define una excepción base para el dominio del proyecto y subclases para cada categoría de error. Esto permite capturar errores a diferentes niveles de granularidad sin usar `except Exception`.

**Cuándo aplica:** siempre que el código lance más de un tipo de error de dominio distinto.

```python
# exceptions.py — módulo compartido del proyecto
class ProjectError(Exception):
    """Excepción base del proyecto. Captura todo lo del dominio sin capturar bugs."""

class InputError(ProjectError):
    """Los datos de entrada son inválidos o no se pueden leer."""

class InputNotFoundError(InputError):
    """El recurso de entrada no existe."""

class InputMalformedError(InputError):
    """El recurso existe pero su estructura es inválida."""

class ServiceError(ProjectError):
    """Error en la comunicación con un servicio externo."""

class ProcessingError(ProjectError):
    """Error durante el procesamiento principal."""
```

Con esta jerarquía, `main()` puede capturar `ProjectError` para todo el dominio, y funciones específicas pueden capturar solo `InputError` o `ServiceError` según su responsabilidad.

```python
# Captura granular en funciones de dominio
try:
    data = load_input(path)
except InputNotFoundError as exc:
    log.error("Recurso no encontrado: %s", exc)
    sys.exit(2)

# Captura amplia solo en el punto de entrada
try:
    run(config)
except ProjectError as exc:
    log.critical("Error irrecuperable: %s", exc, exc_info=True)
    sys.exit(1)
```

### OO3 — Usa el patrón Strategy para comportamientos intercambiables

Cuando una función recibe un parámetro que selecciona entre N implementaciones de la misma operación — un `if/elif` que crece con cada nuevo tipo — extrae cada implementación como un objeto que cumple un protocolo común.

**Cuándo aplica:** cuando el `if/elif` sobre un tipo ha crecido más de dos veces, o cuando se anticipa que seguirá creciendo.

```python
# MAL — la función crece con cada nuevo formato
def render(data: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(data)
    elif fmt == "csv":
        ...
    elif fmt == "xml":   # ← hay que tocar esta función para añadir un formato
        ...

# BIEN — Protocol + registro; añadir un formato no toca el código existente
from typing import Protocol

class Renderer(Protocol):
    def render(self, data: dict) -> str: ...

class JsonRenderer:
    def render(self, data: dict) -> str:
        return json.dumps(data)

class CsvRenderer:
    def render(self, data: dict) -> str:
        ...

RENDERERS: dict[str, Renderer] = {
    "json": JsonRenderer(),
    "csv": CsvRenderer(),
}

renderer = RENDERERS.get(fmt)
if renderer is None:
    raise ValueError(f"Formato desconocido: {fmt!r}")
output = renderer.render(data)
```

### OO4 — Usa el patrón Repository para aislar el acceso a datos

Si varias partes del código leen de la misma fuente de datos, centraliza ese acceso en una clase Repository. El resto del código habla con el Repository, no con la fuente directamente. Esto permite cambiar la fuente (filesystem → base de datos → API) sin tocar la lógica de negocio.

**Cuándo aplica:** cuando más de dos módulos leen del mismo tipo de fuente, o cuando la fuente puede cambiar.

```python
# MAL — acceso a la fuente disperso en múltiples módulos
# En módulo A:
data = Path("store/item.json").read_text()
# En módulo B:
data = Path("store/item.json").read_text()
# En módulo C:
path = Path("store") / name / "item.json"
data = path.read_text()

# BIEN — un solo punto de acceso; los módulos A, B, C dependen del Repository
class ItemRepository:
    def __init__(self, store_dir: Path):
        self._dir = store_dir

    def read(self, name: str) -> dict:
        path = self._dir / name / "item.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, name: str) -> bool:
        return (self._dir / name / "item.json").exists()

    def list_all(self) -> list[str]:
        return sorted(p.parent.name for p in self._dir.rglob("item.json"))
```

### OO5 — Usa `Protocol` en vez de herencia para definir contratos

Cuando necesitas que múltiples clases cumplan una interfaz, define el contrato con `typing.Protocol`. Esto permite duck typing verificado estáticamente sin herencia forzada — cualquier clase que tenga los métodos correctos cumple el protocolo automáticamente.

**Cuándo aplica:** siempre que vayas a escribir una clase base abstracta con métodos `abstractmethod`. Prefiere `Protocol` sobre `ABC` en casi todos los casos.

```python
# MAL — herencia forzada; las implementaciones quedan acopladas a la base
from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    @abstractmethod
    def process(self, data: str) -> str: ...

class ConcreteProcessor(BaseProcessor):   # obligado a heredar
    def process(self, data: str) -> str: ...

# BIEN — Protocol; cualquier clase con el método correcto es compatible
from typing import Protocol

class Processor(Protocol):
    def process(self, data: str) -> str: ...

class ConcreteProcessor:   # no hereda nada
    def process(self, data: str) -> str: ...

# El type checker verifica la compatibilidad sin herencia
def run(processor: Processor, data: str) -> str:
    return processor.process(data)
```

### OO6 — No uses clases donde las funciones son suficientes

Una clase con un solo método público y sin estado entre llamadas es una función disfrazada. Las funciones son más simples, más fáciles de testear y no requieren instanciación.

**Criterio para usar una clase:** el objeto tiene **estado que persiste entre llamadas** o **agrupa múltiples operaciones relacionadas sobre los mismos datos**. Si ninguna condición aplica, usa una función.

```python
# MAL — clase sin estado real
class DataProcessor:
    def run(self, data: dict) -> dict:
        return transform(data)

processor = DataProcessor()
result = processor.run(data)

# BIEN — función directa
def process_data(data: dict) -> dict:
    return transform(data)

result = process_data(data)

# BIEN — clase con estado real (mantiene conexión entre llamadas)
class ApiClient:
    def __init__(self, base_url: str, token: str):
        self._base_url = base_url
        self._session = _create_session(token)   # estado persistente

    def fetch(self, endpoint: str) -> dict: ...
    def post(self, endpoint: str, body: dict) -> dict: ...
```

---

## Logging

El logging es observabilidad permanente, no andamiaje temporal. Un mensaje que se añade para debuggear y luego se elimina indica que el sistema de logging no estaba bien definido. Estas reglas establecen una estrategia estable que funciona en desarrollo y en CI sin modificar el código entre entornos.

### L1 — Usa `logging` de stdlib, nunca `print` para diagnóstico

`print` está reservado exclusivamente para la salida que el caller espera consumir programáticamente (JSON estructurado, CSV, texto formateado que se redirige a otro proceso). Todo lo demás — progreso, advertencias, errores internos, información de debug — usa el módulo `logging`.

```python
# MAL — diagnóstico mezclado con print
print(f"Error procesando {item}: {exc}", file=sys.stderr)
print(f"Procesando item {item_id}...", file=sys.stderr)

# BIEN — logging con nivel y contexto
log.error("Error procesando item %s", item, exc_info=exc)
log.info("Procesando item %s", item_id)
```

### L2 — Un logger por módulo, nombrado con `__name__`

Cada módulo declara su propio logger al inicio del archivo. El nombre `__name__` produce jerarquías automáticas que permiten filtrar por módulo desde la configuración, sin tocar el código.

```python
# Al inicio de cada módulo, después de los imports
import logging

log = logging.getLogger(__name__)

# Nunca uses el root logger directamente en módulos de librería
logging.warning("mensaje")   # MAL — contamina el root logger
log.warning("mensaje")       # BIEN — namespaced al módulo
```

### L3 — Usa el nivel correcto para cada tipo de mensaje

La selección de nivel no es opcional ni subjetiva. Cada nivel tiene una semántica precisa:

| Nivel | Cuándo usarlo |
|---|---|
| `DEBUG` | Detalles internos útiles solo para diagnosticar un bug concreto: valores de variables, paths intermedios, decisiones de ramificación |
| `INFO` | Eventos normales del flujo que confirman que el sistema funciona: inicio de operaciones, ítems procesados, archivos escritos |
| `WARNING` | Algo inesperado que no impide continuar pero merece atención: configuración ausente con fallback, campo opcional faltante, degradación de funcionalidad |
| `ERROR` | Fallo concreto en una operación que aborta esa operación (no el proceso): excepción capturada, recurso no encontrado, respuesta inválida de un servicio |
| `CRITICAL` | Fallo que hace imposible continuar el proceso completo: no se puede inicializar el sistema, dependencia crítica ausente |

```python
log.debug("Estado interno: variable=%s resultado=%s", var, result)
log.info("Operación completada: item=%s duración=%.2fs", item_id, elapsed)
log.warning("Configuración opcional ausente; usando valor por defecto: %s", default)
log.error("Fallo al procesar item %s", item_id, exc_info=True)
log.critical("No se puede inicializar el sistema", exc_info=True)
```

### L4 — Configura el logging una sola vez, en `main()`

La configuración del logging (nivel, formato, handlers) ocurre exactamente una vez, en `main()`, antes de cualquier otra operación. Los módulos de librería **nunca** configuran el logging — solo lo usan. Un módulo que llama a `logging.basicConfig()` o añade handlers rompe la configuración del proceso que lo importa.

```python
# MAL — módulo de librería configurando el logger
logging.basicConfig(level=logging.DEBUG)   # ← contamina al importador

# BIEN — configuración solo en el punto de entrada
def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)

def main() -> None:
    args = _parse_args()
    _configure_logging(verbose=args.verbose)
    ...
```

### L5 — Todos los CLIs tienen el flag `--verbose` / `-v`

Todos los scripts con `argparse` exponen un flag `--verbose` (o `-v`) que activa el nivel `DEBUG`. En ausencia del flag, el nivel por defecto es `INFO`. Esto reemplaza el patrón de añadir y quitar prints temporales: los mensajes de debug siempre están en el código, solo se activan cuando se necesitan.

```python
ap.add_argument(
    "--verbose", "-v",
    action="store_true",
    help="Activa logging DEBUG (detalles internos de ejecución).",
)
```

En CI el flag no se pasa por defecto. En desarrollo, `script.py --verbose` muestra todo el detalle sin cambiar una sola línea de código.

### L6 — Loggea excepciones con `exc_info=True`, no con f-strings manuales

Pasar `exc_info=True` incluye el traceback completo en el log. Un f-string con `{type(exc).__name__}: {exc}` solo da el mensaje, sin contexto de dónde ocurrió el error.

```python
# MAL — pierde el traceback
log.error("Error: %s: %s", type(exc).__name__, exc)

# BIEN — traceback completo incluido automáticamente
log.error("Fallo al procesar %s", item_id, exc_info=True)

# También válido dentro de un bloque except
except ValueError as exc:
    log.error("Valor inválido en %s", context, exc_info=exc)
```

### L7 — Los mensajes de log usan `%s`, no f-strings

El módulo `logging` aplica el formato `%s` de forma lazy — solo si el mensaje va a ser emitido según el nivel activo. Con f-strings, el string se construye siempre, aunque el nivel esté desactivado.

```python
# MAL — expresión evaluada siempre, aunque DEBUG esté desactivado
log.debug(f"items={[item.name for item in collection]}")

# BIEN — evaluado solo si DEBUG está activo
log.debug("items=%s", [item.name for item in collection])
```

### L8 — Separa la salida estructurada del logging

Si el proceso produce salida que otro proceso va a consumir (JSON, CSV, texto formateado), esa salida va a `stdout` mediante `print`. El logging siempre va a `stderr`. Las dos streams nunca se mezclan.

```python
# stdout — salida estructurada que el caller consume
print(json.dumps(result, indent=2, ensure_ascii=False))

# stderr — logging legible para humanos (vía handler configurado en main())
log.info("Proceso completado: %d ítems procesados", count)
```

### L9 — El formato del log se adapta al entorno

En CI el formato es plano y sin colores para que los logs sean parseables. En desarrollo puede incluir timestamps o colores. La detección del entorno ocurre en `_configure_logging()`, nunca en los módulos de librería.

```python
def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    in_ci = os.getenv("CI") == "true"
    fmt = (
        "%(levelname)-8s %(name)s — %(message)s"
        if in_ci else
        "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    )
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt="%H:%M:%S"))
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)
```

---

## Gestión de prompts

Los prompts son lógica de negocio, no strings de configuración. Un prompt hardcodeado dentro de una función es tan problemático como una query SQL incrustada en un controlador: imposible de versionar de forma aislada, imposible de testear sin ejecutar la función completa, y difícil de mantener cuando el modelo o los requisitos cambian.

### PM1 — Los prompts estáticos son constantes nombradas, nunca strings inline

Un prompt que no cambia entre invocaciones es una constante. Vive al inicio del módulo (o en `prompts.py`), con nombre en `UPPER_SNAKE_CASE` que describa su **rol en el sistema**. El sufijo `_SYSTEM_PROMPT` o `_USER_PROMPT` es obligatorio para hacer explícito el rol del mensaje en la conversación con el modelo.

```python
# MAL — string inline invisible desde fuera de la función
def evaluate(adapter, data):
    resp = adapter.invoke(
        "Eres un evaluador. Responde solo JSON...",
        build_message(data)
    )

# MAL — nombre que describe la implementación, no el rol
STRICT_JSON_CHECKER = "Eres un evaluador..."

# BIEN — nombre que describe el rol; sufijo que indica su posición en la conversación
EVALUATOR_SYSTEM_PROMPT = "Eres un evaluador..."
ROUTER_SYSTEM_PROMPT = "Eres un router..."
SUMMARIZER_SYSTEM_PROMPT = "Eres un resumidor..."
```

### PM2 — Los prompts dinámicos se construyen en funciones `build_*_message()` dedicadas

Cuando un prompt necesita datos en tiempo de ejecución, su construcción vive en una función exclusivamente dedicada a eso. La función que invoca al LLM **no** construye el prompt — lo recibe ya construido. Esto permite testear la construcción del mensaje sin llamar al modelo.

```python
# MAL — construcción e invocación mezcladas en la misma función
def evaluate(adapter, item, context=""):
    parts = [f"ITEM:\n{item}"]
    if context:
        parts.append(f"CONTEXTO:\n{context[:4000]}")
    msg = "\n\n".join(parts)
    return adapter.invoke(EVALUATOR_SYSTEM_PROMPT, msg)

# BIEN — construcción separada de invocación
def build_evaluator_message(item: str, context: str = "") -> str:
    """Construye el mensaje de usuario para el evaluador."""
    parts = [f"ITEM:\n{item}"]
    if context:
        parts.append(f"CONTEXTO:\n{context[:_MAX_CONTEXT_CHARS]}")
    return "\n\n".join(parts)

def evaluate(adapter: LLMAdapter, item: str, context: str = "") -> EvalResult:
    """Invoca el evaluador. No construye el prompt."""
    message = build_evaluator_message(item, context)
    resp = adapter.invoke(EVALUATOR_SYSTEM_PROMPT, message)
    return _parse_eval_response(resp)
```

### PM3 — Todos los prompts del proyecto viven en `prompts.py`

Los prompts tienen ciclo de vida propio: se iteran, se versionan y se ajustan independientemente del código que los usa. Dispersarlos en múltiples módulos hace imposible auditar qué instrucciones está recibiendo el modelo. Un módulo `prompts.py` centraliza todas las constantes `*_PROMPT` y las funciones `build_*_message()`.

```
project/
├── prompts.py       ← todas las constantes *_PROMPT y funciones build_*_message()
├── runner.py        ← importa desde prompts.py, no define prompts propios
├── evaluator.py     ← importa desde prompts.py
└── ...
```

```python
# prompts.py
"""Todos los prompts del proyecto.

Convenciones:
- *_SYSTEM_PROMPT: instrucciones de rol para el modelo (mensaje system).
- *_USER_PROMPT: plantillas de mensaje de usuario estáticas.
- build_*_message(): construye mensajes de usuario con datos dinámicos.
- _MAX_*_CHARS: límites de truncado de contexto (constantes privadas).
"""
```

### PM4 — Documenta el formato de respuesta esperado junto al prompt

El prompt que pide una respuesta en cierto formato y el código que parsea esa respuesta son un contrato. Si el formato cambia en el prompt pero no en el parser, el fallo es silencioso. La documentación del formato vive como comentario inmediatamente antes de la constante.

```python
# Formato de respuesta esperado:
# {
#   "result": "pass" | "fail",
#   "reason": "string explicando la decisión"
# }
EVALUATOR_SYSTEM_PROMPT = (
    "Eres un evaluador..."
)
```

Si el proyecto usa `@dataclass` para los resultados del LLM, el dataclass mismo sirve como documentación viva del contrato.

### PM5 — Los límites de contexto son constantes nombradas, no literales mágicos

Los truncados de contexto (`[:4000]`, `[:8000]`, `[:500]`) son decisiones de diseño con impacto directo en la calidad de las respuestas. Deben ser constantes nombradas privadas del módulo `prompts.py`, no literales dispersos en las funciones `build_*`.

```python
# MAL — literales mágicos sin nombre ni justificación
parts.append(f"CONTEXTO:\n{context[:4000]}")
parts.append(f"OUTPUT:\n{output[:8000]}")

# BIEN — constantes nombradas que explican el propósito del límite
# Ajustar si el modelo objetivo tiene ventana de contexto mayor.
_MAX_CONTEXT_CHARS = 4_000
_MAX_OUTPUT_CHARS = 8_000

def build_evaluator_message(item: str, context: str = "", output: str = "") -> str:
    parts = [f"ITEM:\n{item}"]
    if context:
        parts.append(f"CONTEXTO:\n{context[:_MAX_CONTEXT_CHARS]}")
    if output:
        parts.append(f"OUTPUT:\n{output[:_MAX_OUTPUT_CHARS]}")
    return "\n\n".join(parts)
```

### PM6 — El estilo de etiquetas y separadores es consistente entre todos los prompts

El formato interno del mensaje de usuario (cómo se separan las secciones, cómo se etiquetan) debe ser uniforme en todos los `build_*_message()` del proyecto. Prompts con formatos distintos producen respuestas menos predecibles.

```python
# Elige un estilo y aplícalo en todos los build_*_message() del proyecto.
# Ejemplo de estilo con etiquetas en MAYÚSCULAS y separador de doble newline:

def build_evaluator_message(item: str, context: str = "") -> str:
    parts = [f"ITEM:\n{item}"]
    if context:
        parts.append(f"CONTEXTO:\n{context[:_MAX_CONTEXT_CHARS]}")
    return "\n\n".join(parts)   # ← separador consistente

def build_router_message(query: str, candidates: list[str]) -> str:
    parts = [
        f"QUERY:\n{query}",
        f"CANDIDATOS:\n" + "\n".join(f"- {c}" for c in candidates),
    ]
    return "\n\n".join(parts)   # ← mismo separador
```

### PM7 — Los prompts de sistema dinámicos usan `build_*_system_prompt()`

Si el mensaje de sistema varía entre invocaciones (porque incluye una lista de candidatos, configuración por tenant, o contexto de sesión), su construcción vive en una función `build_*_system_prompt()` dedicada — no en un f-string en el callsite. La distinción entre la parte fija y la parte variable debe ser evidente en el código.

```python
# MAL — sistema construido con f-string en el punto de invocación;
# imposible saber qué parte es fija y qué parte varía
adapter.invoke(
    f"Eres un router. Opciones disponibles: {', '.join(options)}. Elige una.",
    user_message
)

# BIEN — función dedicada; la parte fija y la dinámica están separadas
_ROUTER_SYSTEM_TEMPLATE = (
    "Eres un router. Tu única tarea es elegir la opción más apropiada.\n"
    "Responde SOLO un JSON: {{\"choice\": \"<nombre-exacto>\"}}."
)

def build_router_system_prompt(options: list[str]) -> str:
    """El prompt de sistema incluye las opciones disponibles en esta invocación."""
    options_block = "\n".join(f"- {opt}" for opt in options)
    return f"OPCIONES DISPONIBLES:\n{options_block}\n\n{_ROUTER_SYSTEM_TEMPLATE}"
```

---

## Testing

La testabilidad es la justificación de media docena de reglas anteriores —dominio puro (G5), sin
estado mutable al importar (P5), sin `SystemExit` fuera de `main()` (P3), funciones en vez de
clases sin estado (OO6)—. Esta sección dice qué hacer con eso: **las pruebas se escriben desde el
primer commit, no cuando el módulo «esté terminado»**.

### T1 — El dominio puro se prueba sin dobles, sin disco y sin red

Si una regla de negocio necesita un doble de test, un `tmp_path` o un servidor levantado, la regla
no está en `domain/`: está mezclada con I/O y hay que separarla primero. Una prueba de dominio
recibe datos y compara el resultado.

```python
# MAL — la "prueba de dominio" necesita disco, así que la regla no es pura
def test_skill_sin_description(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\n---\n")
    assert validate_repository(tmp_path).errors

# BIEN — la regla recibe datos y devuelve hallazgos
def test_sin_description_es_error():
    findings = review_skill("x", "mi-skill", {"name": "mi-skill", "description": ""}, 10)
    assert any("description" in f.message for f in findings)
```

### T2 — Cada prueba nombra el defecto que cubre, no la función que llama

El nombre de la prueba es lo único que se lee cuando falla en CI. `test_revisar_skill_caso_3` no
dice nada; `test_allowed_tools_como_lista_es_error` dice exactamente qué se rompió y por qué
importaba.

```python
# MAL — el nombre describe la mecánica
def test_revisar_envelope_1(): ...
def test_validador_ok(): ...

# BIEN — el nombre describe el defecto y su severidad
def test_falta_cada_campo_del_envelope_produce_un_error(): ...
def test_una_referencia_no_es_un_secreto(): ...
def test_skill_muy_largo_es_aviso_y_no_bloquea(): ...
```

### T3 — Todo defecto medido se convierte en prueba de regresión

Cuando una suposición se cae al ejecutarla —o un bug aparece en producción— la corrección incluye
la prueba que lo fija. Sin ella, la siguiente persona que «simplifique» el código lo reintroduce
sin enterarse. El comentario de la prueba dice **dónde se midió**, no solo qué comprueba.

```python
def test_version_no_semver_es_error():
    # Medido al instalar el artefacto: `version: "1.0.0"` pierde las comillas al reescribirse; con
    # `1.10` el valor se interpretaría como número y perdería el cero.
    for bad_version in ("1.0", "v1.0.0", "1.10"):
        assert _errors(review_envelope("x", {**ENVELOPE, "version": bad_version})), bad_version
```

### T4 — Los adaptadores se prueban con dobles inyectados, no con *monkeypatching*

Si el caso de uso recibe sus adaptadores como argumentos con un default sobreescribible, la prueba
inyecta un doble y no hace falta parchear módulos. El *monkeypatching* es una señal de que el
cableado está oculto dentro de la función en vez de estar en la firma.

```python
# MAL — parchea el módulo importado; la prueba conoce la implementación interna
def test_validar(monkeypatch):
    monkeypatch.setattr("validator_bcp.adapters.repository.read", lambda *_: FAKE)

# BIEN — el adaptador es un argumento con default; la prueba lo sustituye
def validate(root, *, repository=repository_adapter): ...

def test_validar_con_repositorio_falso():
    assert validate(Path("."), repository=FakeRepository()).is_conformant
```

### T5 — Una prueba comprueba una cosa, y su fallo señala una sola causa

Una prueba con seis aserciones sobre aspectos distintos falla en la primera y esconde las otras
cinco — el mismo problema que los gates que fallan rápido en vez de agregar. Si el caso genuinamente
tiene varias variantes, se recorren en un bucle con el valor en el mensaje de la aserción.

```python
# MAL — falla en la primera y oculta el resto
def test_envelope():
    assert not review_envelope("x", COMPLETE)
    assert _errors(review_envelope("x", WITHOUT_ID))
    assert _errors(review_envelope("x", WITHOUT_OWNER))

# BIEN — el bucle dice cuál falló
def test_falta_cada_campo_del_envelope_produce_un_error():
    for field in ENVELOPE:
        incomplete = {k: v for k, v in ENVELOPE.items() if k != field}
        assert _errors(review_envelope("x", incomplete)), f"no se detectó la falta de {field}"
```

### T6 — El código que decide si algo se publica tiene sus propias pruebas en CI

Un validador, un gate o un generador de índice son infraestructura de la que dependen todos los
consumidores: si se rompen en silencio, dejan de proteger sin que nadie lo note. Sus pruebas corren
en cada cambio que los toque, y son rápidas porque el dominio es puro.

```yaml
on:
  pull_request:
    paths: ["validador/**"]

jobs:
  pruebas:
    steps:
      - name: Ejecutar las pruebas del dominio
        working-directory: validador
        run: python -m pytest tests -q
```

---

## Checklist de revisión

Antes de hacer commit de cualquier cambio, verifica cada punto:

**Arquitectura y responsabilidad**
- [ ] Ningún módulo agrupa más de una responsabilidad (tests de conjunción y de grupos de G1).
- [ ] Ningún archivo Python supera ~300 líneas sin dividirse o sin un comentario que justifique la cohesión.
- [ ] Tras extraer concerns a módulos compartidos, se re-revisó el núcleo restante.
- [ ] El código está en paquetes por capa (domain/application/ports/adapters); la raíz solo tiene entry points.
- [ ] Se respeta la regla de dependencia: domain no importa adapters; application no importa adapters concretos salvo I/O de implementación única documentada.
- [ ] No hay puertos abstractos con una sola implementación (puerto solo donde hay polimorfismo real).
- [ ] Los identificadores nuevos están en inglés y la prosa en español (G3b). No se tocaron los cuatro identificadores del gate, los cinco workflows reutilizables ni las claves ya persistidas en Port o en los esquemas.

**Python**
- [ ] Todos los imports están al inicio del archivo.
- [ ] No hay `except Exception` sin justificación explícita en comentario.
- [ ] No hay `SystemExit` fuera de `main()`.
- [ ] Las funciones no mutan sus argumentos.
- [ ] No hay I/O ni cómputo pesado en el top-level del módulo.
- [ ] Los valores con opciones finitas usan `Enum`, no strings literales.
- [ ] Los tipos de retorno son coherentes; no hay `tuple[bool, X]` con semántica variable.
- [ ] Las funciones internas llevan prefijo `_`.
- [ ] No hay lógica duplicada entre módulos del mismo proyecto.
- [ ] Los comandos externos se construyen con listas, no con concatenación de strings.
- [ ] Los umbrales/límites/topes/timeouts/rondas/top-N son constantes nombradas, no literales mágicos (P11); los defaults de flags de CLI se toman de esa constante.

**Diseño orientado a objetos**
- [ ] Los datos estructurados que viajan entre funciones usan `@dataclass`, no `dict` o `tuple`.
- [ ] Los errores de dominio tienen una jerarquía propia con excepción base del proyecto.
- [ ] Los `if/elif` que crecen con nuevos tipos usan el patrón Strategy con `Protocol`.
- [ ] El acceso a una fuente de datos compartida está centralizado en un Repository.
- [ ] Los contratos entre componentes usan `Protocol`, no herencia de `ABC`.
- [ ] No hay clases sin estado real — las funciones sin estado son funciones, no clases.

**Testing**
- [ ] Las reglas de dominio se prueban sin disco, sin red y sin dobles (T1).
- [ ] Cada prueba nombra el defecto que cubre, no la función que llama (T2).
- [ ] Todo defecto medido tiene su prueba de regresión, con un comentario que dice dónde se midió (T3).
- [ ] Los adaptadores se sustituyen por inyección, no con `monkeypatch` (T4).
- [ ] Ninguna prueba encadena aserciones sobre aspectos distintos; las variantes van en bucle con mensaje (T5).
- [ ] El código que decide si algo se publica —validadores, gates, generadores— tiene pruebas en CI (T6).

**Logging**
- [ ] No hay `print(..., file=sys.stderr)` de diagnóstico — solo `log.*()`.
- [ ] Cada módulo tiene `log = logging.getLogger(__name__)` al inicio.
- [ ] El nivel de cada mensaje es correcto (DEBUG / INFO / WARNING / ERROR / CRITICAL).
- [ ] El logging se configura una sola vez en `main()`, nunca en módulos de librería.
- [ ] Todos los CLIs tienen el flag `--verbose` / `-v`.
- [ ] Las excepciones se loggean con `exc_info=True`, no con f-strings manuales.
- [ ] Los mensajes usan `%s`, no f-strings.
- [ ] La salida estructurada va a `stdout`; el logging siempre a `stderr`.

**Gestión de prompts**
- [ ] No hay strings de prompt inline dentro de funciones.
- [ ] Las constantes tienen sufijo `_SYSTEM_PROMPT` o `_USER_PROMPT`.
- [ ] Los prompts dinámicos se construyen en funciones `build_*_message()` dedicadas.
- [ ] Las funciones que invocan al LLM no construyen prompts — los reciben ya construidos.
- [ ] Todos los prompts y funciones `build_*` están centralizados en `prompts.py`.
- [ ] El formato de respuesta esperado está documentado antes de cada constante de prompt.
- [ ] Los límites de contexto son constantes nombradas, no literales mágicos.
- [ ] El estilo de etiquetas y separadores es consistente entre todos los `build_*_message()`.

**YAML / GitHub Actions**
- [ ] La lógica reutilizable entre workflows está en composite actions, no duplicada.
- [ ] Las versiones de herramientas son variables, no literales hardcodeados.
- [ ] Los inputs con defaults se resuelven una sola vez (env de job o step inicial).
- [ ] Las ramas condicionales complejas son steps separados con `if:` de Actions.
- [ ] Todos los paths son absolutos o consistentes con su `working-directory`.
- [ ] Los steps con `continue-on-error` capturan y exponen su outcome.
- [ ] Las exclusiones de globs son explícitas con `!`, no implícitas por estructura.
- [ ] Los nombres de steps describen el resultado y el contexto, no solo la acción.

---

# Parte 2. Reglas de los componentes de este repositorio

## Reglas de repositorio

- **Un workflow por evento, un job por responsabilidad.** Los llamadores de los dominios no llevan
  lógica; los reutilizables piden permisos mínimos por job y los recibe del llamador. `@v1` para lo
  propio, SHA para terceros. Ningún workflow supera 150 líneas sin justificación en su cabecera.
- **SDD en cada capacidad.** Ninguna capacidad empieza por el código: `/speckit.specify`, `clarify`,
  `checklist`, `plan`, `tasks`, `analyze`, `implement`. Una spec por capacidad, una rama
  `feat/NNN-<nombre>` y un PR por spec, con la spec enlazada. La prosa de los skills y los documentos
  de diseño se escriben a mano.
- **Medición antes de construir.** Lo que dependa de un comportamiento de Copilot CLI, Claude Code o
  GitHub se mide en el hito donde se necesita y la medición se convierte en prueba de regresión (T3).
- **Sin em-dashes** en ningún documento ni comentario nuevo.

## Asistente de autoría (`plugins/authoring-assistant/`)

- Identificadores en inglés, prosa en español (G3b). Los estados y campos que ya existen en el árbol de
  decisión y las reglas de rama y versión (`main_clean`, `work_branch_clean`, `feat/`, `fix/`,
  `deprecate/`, `risk_level`, entre otros) son contrato: no se renombran.
- Cada script imprime un solo JSON en `stdout` y el diagnóstico en `stderr` (L8). Código de salida 0 si
  pudo clasificar, aunque el estado sea de parada; distinto de 0 sólo si no pudo ejecutar.
- Comandos de git permitidos a los scripts: `fetch`, `switch -c`, `add`, `commit` y `push` **sólo de la
  rama `<accion>/<unidad>` actual**, y `gh pr create` sobre ella. Nunca `stash`, `reset`, `checkout` de
  archivos ajenos ni nada sobre otra rama.
- Todo script que escribe valida que el destino está bajo la raíz de la unidad elegida; ningún script
  lee variables de entorno de credenciales; el que consulta herramientas de un servidor MCP lo arranca
  sólo tras confirmación explícita del autor.
- El dominio no importa `subprocess` ni `pathlib`: versión, riesgo, aprobadores y clasificación del
  diff se prueban con datos, sin repositorio (T1).
- La intención pendiente se guarda en `git config --local`: un clon nuevo no la hereda y en worktrees
  compartidos conviene `--worktree`; queda documentado y probado.
- El `SKILL.md` y los `references/` son prosa revisada a mano contra el árbol de decisión;
  `/speckit.implement` produce código y pruebas, no la guía del diálogo.
