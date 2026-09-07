# Validador del estándar agéntico

Comprueba que una unidad publicable cumple las reglas del estándar. Lo ejecuta el autor en su máquina
antes de pedir revisión, y la automatización en cada push, sin diferencias entre las dos.

## Instalación

```
pip install "git+https://github.com/Banca-Agente-IA-demo/agentic-standard@v0.1.0#subdirectory=validator"
```

La etiqueta fija la versión: el asistente de autoría la lee de `validator.lock` para que la máquina
del autor y la automatización usen exactamente la misma. No es autocontenido; necesita `jsonschema`,
`pyyaml` y `referencing`, así que conviene un entorno propio.

## Uso

```
rules <carpeta-de-la-unidad>
rules <carpeta-de-la-unidad> --format json     # para el asistente
rules <carpeta-de-la-unidad> --verbose         # detalle de lo que lee
```

La carpeta de la unidad es la que contiene `GOVERNANCE.json`. El repositorio que la aloja se deduce
del árbol; `--repository` lo fuerza cuando la unidad no está en su sitio habitual.

| Código de salida | Significado |
|---|---|
| `0` | Cumple: ningún error. Puede haber avisos |
| `1` | No cumple: al menos un error |
| `2` | No se pudo comprobar: la carpeta no existe o no es una unidad |

## Qué comprueba

| Grupo | Reglas |
|---|---|
| Contrato | El archivo de gobierno valida contra `governance.schema.json` |
| Identidad | Gobierno e identidad presentes; el identificador empieza por el repositorio y termina en el nombre de la unidad; ese nombre es el del manifiesto y el del directorio; versión SemVer estricta; ningún campo fuera del formato de identidad |
| Permisos (C1) | Las herramientas de cada agente, los ejecutables de cada hook y el servidor de la conexión están declarados en `permissions` |
| Servidor MCP (D2, C2) | Como mucho un servidor; la misma clave en conexión, gobierno y permisos; el bloque de gobierno existe si y sólo si hay conexión; credenciales cotejadas en los dos sentidos; ningún valor literal con pinta de secreto |
| Hooks (D3, C5) | Tope de tiempo en cada acción y con el nombre correcto; comando dentro de la unidad; sin descarga en ejecución; eventos portables (aviso) |
| Artefactos (D1, D7, C3) | Nombre declarado igual al que impone la ruta; descripción no vacía; ningún campo de gobierno en el frontmatter; mapa de catálogo texto a texto; las dos grafías del agente que restringe servidor; tratamiento de contenido externo según el tipo |
| Evaluación (D4) | Si la unidad trae suite: mínimo de casos, las tres categorías, y una aserción mecánica por caso |
| Riesgo (03 §1) | El nivel declarado nunca por debajo del mínimo calculado de hechos |

## Qué no comprueba, a propósito

- **Nada que exija hablar con GitHub**: que el equipo dueño exista, o que hayan aprobado los revisores
  del tipo y del nivel. Eso es del workflow de verificación, que sí tiene sesión autenticada.
- **El contrato real del servidor**: exigiría arrancarlo, y eso sólo se hace tras confirmación
  explícita del autor.
- **La estructura interna de cada tipo**: la fija la herramienta, no el estándar. El validador lee de
  cada formato de cliente sólo lo enumerado arriba.
- **La ausencia de suite**: se exige para publicar, no para registrar.

## Cómo viaja el contrato de gobierno

El esquema existe en un único sitio, `schemas/governance.schema.json` del repositorio, y el
constructor lo inyecta dentro de la distribución al armarla. No hay una segunda copia en el árbol que
pueda derivar. En un clon de trabajo con instalación editable, la inyección todavía no ha ocurrido y
el validador lee el mismo archivo canónico, así que las dos formas de ejecutar validan contra lo
mismo.

## Desarrollo

```
pip install -e ./validator
python -m pytest tests/validator -q
```

Las reglas son funciones puras de una instantánea de la unidad a sus hallazgos, y se prueban con datos
en memoria. El único módulo que toca disco es el que construye la instantánea.
