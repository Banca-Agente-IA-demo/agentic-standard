# Implementation Plan: El validador del estándar y su comando de reglas

**Branch**: `feat/004-validator-rules` | **Date**: 2026-09-07 | **Spec**: [spec.md](spec.md)

## Summary

Un paquete `validator/` con su propio `pyproject.toml`, instalable con
`pip install "git+…#subdirectory=validator"`, que expone el comando `rules`. Recibe la carpeta de una
unidad, la lee una vez a una instantánea inmutable, y pasa esa instantánea por una lista de reglas
puras. Devuelve todos los hallazgos con severidad, archivo y motivo. El contrato de gobierno viaja
dentro del paquete, inyectado en el momento de construir desde el único archivo de `schemas/`.

## Technical Context

**Language/Version**: Python 3.11 mínimo, matriz 3.11 y 3.12 en CI.

**Primary Dependencies**: `jsonschema` y `pyyaml` como dependencias **de ejecución** del paquete, que
es lo que lo hace no autocontenido y obliga al entorno privado que el asistente creará en el hito A0.
Se declara también `referencing`, que la demo usaba sin declarar y le llegaba de rebote.

**Storage**: ninguno. Lee el árbol de la unidad y escribe sólo a las salidas estándar.

**Testing**: `pytest`. Las reglas se prueban con instantáneas construidas en memoria, sin disco ni red
(T1). El lector de disco se prueba con `tmp_path` y con una unidad instanciada de las plantillas.

**Target Platform**: la máquina del autor (Windows con PowerShell incluido) y el runner de CI.

**Project Type**: paquete de biblioteca con interfaz de línea de comandos.

**Constraints**: el validador no habla con GitHub ni arranca servidores. No juzga el contenido de los
formatos de cliente más allá de lo enumerado en la sección 5 de la revisión.

**Scale/Scope**: una unidad por ejecución; decenas de artefactos como mucho.

## Constitution Check

| Puerta | Respuesta | Estado |
|---|---|---|
| (1) Qué decide un script y qué hace el modelo | Todo lo decide el código. El modelo, en el hito 2, leerá un campo del informe. Por eso el comando emite también formato estructurado. | Pasa |
| (2) Qué comandos de git ejecuta y sobre qué rama | Ninguno. El validador no toca git. | Pasa |
| (3) Qué se mide en cada cliente y cómo se convierte en prueba | Las mediciones de D3 y D7 pasan a reglas, cada una con su prueba y el comentario de dónde se midió. La forma de los `${VAR}` y las variables del cliente que se excluyen vienen medidas de la demo. | Pasa |
| (4) Qué es dominio puro y qué adaptador | Paquetes por capa (G5): `domain/` con `model.py` y `rules/`, sin disco ni formatos; `adapters/` con la lectura, el frontmatter, el contrato y el informe; `cli.py` como único composition root. Sin `ports/`, justificado abajo y en el docstring de `cli.py`. Hay pruebas de arquitectura que lo comprueban. | Pasa |
| (5) Qué nombres nuevos son contrato | El nombre del comando `rules`, el de la distribución, los identificadores de regla que aparecen en cada hallazgo y los códigos de salida. | Pasa |
| (6) Qué escribe cada script y dónde | Nada en disco. Informe a la salida estándar, diagnóstico a la de error. | Pasa |
| (7) Qué eventos y jobs añade cada workflow | Ninguno nuevo aquí. Se amplían las rutas del workflow de pruebas para cubrir `validator/`. El workflow reutilizable de registro es la spec 005. | Pasa |

## Project Structure

### Documentation (this feature)

```text
specs/004-validator-rules/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
validator/
├── pyproject.toml               distribución propia; inyecta ../schemas en el paquete al construir
├── README.md                    qué comprueba, cómo se instala, cómo se ejecuta
└── agentic_validator/
    ├── __init__.py
    ├── cli.py                   composition root: argumentos, cableado, código de salida
    ├── domain/                  puro: sin disco, sin red, sin formatos
    │   ├── model.py             severidad, hallazgo, informe, nivel de riesgo, instantánea
    │   └── rules/               una responsabilidad por módulo
    │       ├── __init__.py      la lista ALL_RULES y el recorrido
    │       ├── identity.py      repositorio, nombre, versión, campos del manifiesto
    │       ├── permissions.py   herramientas, ejecutables y servidor contra lo declarado
    │       ├── mcp.py           un servidor por unidad, claves emparejadas, credenciales
    │       ├── hooks.py         tope de tiempo, ruta, descarga, eventos portables
    │       ├── artifacts.py     nombre y descripción de cada artefacto; suite si la trae
    │       └── risk.py          mínimo calculado y comparación con lo declarado
    ├── adapters/                todo lo que toca el exterior
    │   ├── reading.py           de la carpeta de la unidad a la instantánea
    │   ├── frontmatter.py       ayudante compartido: frontmatter de un archivo de texto
    │   ├── contract.py          carga del esquema y validación contra él
    │   └── report.py            informe legible y estructurado
    └── schemas/                 lo pone el constructor desde ../schemas; no está en el árbol

tests/validator/
├── __init__.py
├── units.py                     unidades en disco e instantáneas en memoria para las pruebas
├── test_rules_identity.py
├── test_rules_permissions.py
├── test_rules_mcp.py
├── test_rules_hooks.py
├── test_rules_artifacts.py
├── test_rules_risk.py
├── test_end_to_end.py           una unidad instanciada de las plantillas, en tmp_path
├── test_architecture.py         regla de dependencia, pureza del dominio y umbral de tamaño
└── test_packaging.py            el contrato de gobierno del paquete es el del repositorio
```

**Structure Decision**: `validator/` es una distribución aparte porque se instala sola, fijada por
etiqueta, en la máquina del autor. El paquete de herramientas de la raíz y éste conviven sin
mezclarse. Dentro, paquetes por capa como exige G5: `domain/` puro, `adapters/` con todo el exterior,
y la raíz sólo con el entry point. **Sin `ports/`**: no hay polimorfismo ni doble de test que lo
justifique, porque la lectura de disco tiene una sola implementación y las reglas reciben la
instantánea ya construida; G5 prohíbe el puerto especulativo. La justificación queda escrita en el
docstring de `cli.py`, y hay pruebas de arquitectura que comprueban la regla de dependencia, la
pureza del dominio y el umbral de tamaño de cada módulo.

**Cómo viaja el contrato de gobierno**: D5 exige que el esquema exista en un único sitio,
`schemas/governance.schema.json`, y que viaje como dato dentro del paquete. El constructor del paquete
lo inyecta desde `../schemas` al armar la distribución, así que no hay una segunda copia en el árbol
que pueda derivar. Se comprueba con una prueba que compara el archivo del paquete construido con el
del repositorio.

## Qué se reutiliza de la demo, y qué no

Del inventario del validador anterior (7.144 líneas):

| Pieza | Decisión |
|---|---|
| Detección de `${VAR}` en `env` y `headers`, con sus prefijos y las variables del cliente que se excluyen | **Reutilizar la forma**, en inglés. Es conocimiento medido sobre el formato |
| Cotejo de credenciales en los dos sentidos | **Reutilizar la idea**: usada y no declarada es error, declarada y no usada es error |
| Severidad y hallazgo con dos niveles | **Reutilizar la forma**, en inglés |
| Lector de frontmatter | **Rehacer más corto**. Las 194 líneas de la demo incluyen una extracción degradada por expresiones regulares para cuando el YAML es inválido, que existía para el ensamblado retirado. Aquí un frontmatter inválido es un hallazgo, no algo que rescatar |
| Lector de tres formas de `mcpServers` | **No reutilizar**. Aquellas formas eran del catálogo público; una unidad del estándar declara `mcpServers` y como mucho un servidor (D2) |
| Cálculo de riesgo | **No existe en la demo**: se escribe entero |
| Ensamblado, política, ficha, proyección, especificación, digesto, deriva, orquestador de 737 líneas | **Descartar**: describen el diseño retirado |

La demo declaraba `jsonschema` y `pyyaml` pero usaba `referencing` sin declararlo, y le llegaba de
rebote. Aquí se declara.

## Complexity Tracking

Sin violaciones que justificar. El único punto que merece explicación, y está arriba, es la inyección
del esquema al construir: la alternativa era una segunda copia en el árbol con una prueba que vigilase
la divergencia, y evitar la copia es mejor que vigilarla.
