"""Se hace cargo del vocabulario fijo del estándar: los nombres, los umbrales y las escalas.

Es lo que el estándar fija por contrato y ninguna regla puede redefinir por su cuenta. Vive aparte de
`adapters/contract.py`, que no fija nada: aquel comprueba un documento contra el esquema JSON y por
tanto es entrada y salida. Esto es dominio puro, así que el nombre `contract` no se reutiliza aquí
para que la capa a la que pertenece cada uno se lea en el import.
"""

from __future__ import annotations

from enum import Enum

GOVERNANCE_FILE = "GOVERNANCE.json"
MANIFEST_FILE = ".claude-plugin/plugin.json"
MCP_FILE = ".mcp.json"
HOOKS_FILE = "hooks/hooks.json"
EVALS_DIR = "evals"

# El formato de plugin permite estos campos de primer nivel. El estándar no publica un esquema suyo:
# es formato ajeno y una copia derivaría (revisión del hito 1 §3).
ALLOWED_MANIFEST_FIELDS = frozenset(
    {"$schema", "name", "version", "description", "author", "repository", "license", "keywords", "homepage", "category"}
)

# Eventos que disparan en los dos clientes con la misma grafía, medidos el 7 de septiembre de 2026
# (D3). Uno fuera de la lista no falla en el cliente: no dispara nunca, y el autor cree que su control
# está activo. Avisa hasta que el lineamiento 04 §2 fije la lista.
PORTABLE_HOOK_EVENTS = frozenset(
    {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"}
)

# Variables que expande el cliente, no credenciales: aparecen como ${VAR} y no se cuentan (medido en
# la demo anterior).
CLIENT_VARIABLES = frozenset(
    {"CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "workspaceFolder"}
)
PLUGIN_ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"

# Tope de tiempo de un hook, en segundos. El lineamiento 04 §2 exige que exista un techo pero todavía
# no fija el número; éste es el del estándar hasta que lo haga. Un hook que tarde más cuelga la sesión
# de quien lo instaló sin que pueda saber por qué.
MAX_HOOK_TIMEOUT_SECONDS = 60

# Límite de la descripción que fija la especificación de skills. Es lo único que se carga en CADA
# petición, así que pasarse degrada la selección de todos los artefactos instalados.
MAX_DESCRIPTION_LENGTH = 1024

HOOK_TESTS_DIR = "hooks/tests"

# --- Higiene del contenido versionado (C2) --------------------------------------------------------

# Extensiones que se juzgan como configuración o código ejecutable. En la prosa de un documento una
# ruta o una asignación suelen ser un ejemplo, así que las reglas que miran la FORMA del valor se
# limitan a estas; las que reconocen un token de proveedor por su prefijo miran todo, porque ahí no
# hay ambigüedad posible.
CONFIGURATION_SUFFIXES = (".json", ".yaml", ".yml", ".sh", ".ps1", ".py", ".bat")

# Longitud a partir de la cual un valor sin variable deja de parecer un identificador y empieza a
# parecer una credencial.
MIN_SECRET_VALUE_LENGTH = 12

# Caracteres distintos que exige un valor para contar como entropía alta. Un digesto de ejemplo con
# ceros, un `xxxxxxxxxxxx` o un `changeme-changeme` se quedan por debajo y no disparan.
MIN_SECRET_DISTINCT_CHARS = 10

# Claves de un mapa de conexión que suelen llevar credencial. La lista es amplia a propósito: ahí el
# contexto ya es estrecho, porque sólo se miran `env` y `headers` del servidor.
SECRET_LIKE_CONNECTION_KEYS = ("authorization", "token", "secret", "password", "api_key", "apikey", "key")

# Claves que delatan una credencial cuando aparecen asignadas en cualquier archivo. La lista es más
# estrecha que la anterior y deja fuera `key` a secas: un `key:` de un mapa cualquiera es demasiado
# común para bloquear por él.
SECRET_ASSIGNMENT_KEYS = (
    "api_key",
    "apikey",
    "api-key",
    "access_key",
    "private_key",
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
)

# Carpetas de apoyo de un artefacto: material que viaja en el paquete para que el artefacto lo use.
# No hay lista blanca de lo que puede haber dentro, sólo de dónde se busca.
SUPPORT_DIRECTORIES = ("references", "assets", "scripts", "templates", "examples")

DETERMINISTIC_ASSERT_TYPES = frozenset(
    {"contains", "icontains", "not-contains", "regex", "is-json", "javascript"}
)
REQUIRED_EVAL_CATEGORIES = frozenset({"happy_path", "edge_case", "negative"})
MIN_EVAL_CASES = 3

# Clasificaciones de dato que elevan el riesgo mínimo al nivel más alto (03 §1).
SENSITIVE_CLASSIFICATIONS = frozenset({"confidential", "restricted"})


class RiskLevel(str, Enum):
    """La escala de riesgo de 03 §1, que decide quién aprueba y por cuánto tiempo."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {"low": 0, "medium": 1, "high": 2}[self.value]
